#!/usr/bin/env python3
"""Prisma Access 5G SASE Management CLI Tool.

CLI utility to inspect, create, update, and delete SIM cards (UE) and real-time subscriber sessions.
"""

import argparse
import sys
import json
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.config import load_config
from src.client import Prisma5GClient
from src.models import UESession

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prisma Access 5G SASE CLI Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--env",
        dest="env_file",
        help="Path to .env file (default: ./.env)",
        default=None,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # 0. tenants
    subparsers.add_parser("tenants", help="List all Tenant Service Groups (Root & Child Tenants)")

    # 1. list
    list_p = subparsers.add_parser("list", help="List registered SIM cards / Tenant UEs")
    list_p.add_argument("--tsg-id", help="Filter by specific TSG ID (default: all child tenants)")
    list_p.add_argument("--tenant", help="Filter by tenant name (e.g. 'Transatel demo')")
    list_p.add_argument("--page", type=int, default=0, help="Page number (default 0)")
    list_p.add_argument("--size", type=int, default=50, help="Page size (default 50)")
    list_p.add_argument("--filter", dest="filter_query", help="Filter (e.g. apn:internet.panw.com)")
    list_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # 2. get
    get_p = subparsers.add_parser("get", help="Get a single Tenant UE by ID")
    get_p.add_argument("id", help="UE Identity ID or UUID")
    get_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # 3. add
    add_p = subparsers.add_parser("add", help="Register a new SIM card (Tenant UE mapping + optional session IP)")
    add_p.add_argument("--imsi", required=True, help="15-digit IMSI number")
    add_p.add_argument("--imei", required=True, help="15-digit IMEI number")
    add_p.add_argument("--apn", help="APN name (default from .env)")
    add_p.add_argument("--tsg-id", help="Child TSG ID to attach SIM to")
    add_p.add_argument("--tenant", help="Child Tenant name (e.g. 'Transatel demo')")
    add_p.add_argument("--root-tsg-id", help="Root TSG ID (auto-detected if omitted)")
    add_p.add_argument("--ip", "--ipv4", dest="ipv4", help="Optional IPv4 address to immediately activate/register the 5G subscriber session")
    add_p.add_argument("--ipv6", help="Optional IPv6 address for subscriber session")
    add_p.add_argument("--ip-type", default="IPv4", choices=["IPv4", "IPv6", "IPv4v6"], help="IP Type (default: IPv4)")
    add_p.add_argument("--msisdn", help="Optional MSISDN phone number")
    add_p.add_argument("--slice-id", help="Optional Network Slice ID")

    # 4. update
    update_p = subparsers.add_parser("update", help="Update an existing Tenant UE mapping")
    update_p.add_argument("id", help="UE Identity ID")
    update_p.add_argument("--imsi", help="Updated IMSI number")
    update_p.add_argument("--imei", help="Updated IMEI number")
    update_p.add_argument("--apn", help="Updated APN name")
    update_p.add_argument("--tsg-id", help="Updated TSG ID")
    update_p.add_argument("--group-id", help="Assign to subscriber group ID (or 'none' to unassign)")

    # 5. delete
    del_p = subparsers.add_parser("delete", help="Delete a registered SIM card / Tenant UE mapping")
    del_p.add_argument("id", help="UE Identity ID to delete")

    # 6. bulk-delete
    bulk_del_p = subparsers.add_parser("bulk-delete", help="Bulk delete multiple Tenant UEs")
    bulk_del_p.add_argument("ids", nargs="+", help="One or more UE Identity IDs")

    # 7. session-register
    s_reg = subparsers.add_parser("session-register", help="Register real-time 5G subscriber session")
    s_reg.add_argument("--imsi", required=True, help="15-digit IMSI")
    s_reg.add_argument("--imei", required=True, help="15-digit IMEI")
    s_reg.add_argument("--apn", required=True, help="APN name")
    s_reg.add_argument("--ip-type", default="IPv4", choices=["IPv4", "IPv6", "IPv4v6"], help="IP Type")
    s_reg.add_argument("--ipv4", help="Allocated IPv4 address")
    s_reg.add_argument("--ipv6", help="Allocated IPv6 address")
    s_reg.add_argument("--msisdn", help="MSISDN phone number")
    s_reg.add_argument("--cell-id", help="Cell ID")
    s_reg.add_argument("--slice-id", help="Network Slice ID")

    # 8. session-terminate
    s_term = subparsers.add_parser("session-terminate", help="Terminate real-time 5G subscriber session")
    s_term.add_argument("--imsi", required=True, help="15-digit IMSI")
    s_term.add_argument("--imei", required=True, help="15-digit IMEI")
    s_term.add_argument("--apn", required=True, help="APN name")
    s_term.add_argument("--ip-type", default="IPv4", choices=["IPv4", "IPv6", "IPv4v6"], help="IP Type")
    s_term.add_argument("--ip", "--ipv4", dest="ipv4", required=True, help="IPv4 address of the session to terminate")

    # 9. groups
    grp_p = subparsers.add_parser("groups", help="List 5G Subscriber User Groups")
    grp_p.add_argument("--tsg-id", help="Override TSG ID")
    grp_p.add_argument("--group-id", help="Filter by specific Group ID")
    grp_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # 10. group-create
    gc_p = subparsers.add_parser("group-create", help="Create a new 5G Subscriber Identity Group")
    gc_p.add_argument("--name", required=True, help="Group name (e.g. 'VIP-Sensors')")
    gc_p.add_argument("--tsg-id", help="Target TSG ID")
    gc_p.add_argument("--identities", nargs="*", help="Optional initial UE Identity IDs")
    gc_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # 11. group-get
    gg_p = subparsers.add_parser("group-get", help="Get details and member IDs for a User Group")
    gg_p.add_argument("id", help="Group ID")
    gg_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # 12. group-delete
    gd_p = subparsers.add_parser("group-delete", help="Delete a 5G Subscriber User Group")
    gd_p.add_argument("id", help="Group ID to delete")

    # 13. assign-group
    ag_p = subparsers.add_parser("assign-group", help="Assign a SIM / UE to a Subscriber User Group")
    ag_p.add_argument("--ue-id", required=True, help="UE Identity ID")
    ag_p.add_argument("--group-id", help="Target Group ID (or 'none' to unassign)")
    ag_p.add_argument("--group-name", help="Target Group Name (e.g. 'Permissive', 'Restrictive')")
    ag_p.add_argument("--tsg-id", help="TSG ID")

    # 14. summary (SCM Dashboard KPI Stats)
    sum_p = subparsers.add_parser("summary", help="Show 5G SASE Summary Monitoring KPIs (matching Strata Cloud Manager)")
    sum_p.add_argument("--tsg-id", help="Override TSG ID")
    sum_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # 15. interconnect
    ic_p = subparsers.add_parser("interconnect", help="List regional 5G Interconnects, Bandwidth, and VLAN attachments")
    ic_p.add_argument("--tsg-id", help="Override TSG ID")
    ic_p.add_argument("--json", action="store_true", help="Output raw JSON")

    return parser


def handle_tenants(client: Prisma5GClient, args: argparse.Namespace):
    with console.status("[bold green]Discovering Tenant Service Groups..."):
        tenants = client.list_tenants()

    table = Table(title=f"Tenant Service Groups / Hierarchy (Count: {len(tenants)})")
    table.add_column("TSG ID", style="cyan", no_wrap=True)
    table.add_column("Display Name", style="bold green")
    table.add_column("Parent TSG ID", style="blue")
    table.add_column("Type", style="magenta")

    for t in tenants:
        tid = str(t.get("id"))
        p_id = str(t.get("parent_id") or "")
        t_type = "Root (MSP)" if not p_id or p_id == "None" or tid == str(client.config.tsg_id) else "Child Tenant"
        table.add_row(tid, str(t.get("display_name", "")), p_id, t_type)

    console.print(table)


def handle_list(client: Prisma5GClient, args: argparse.Namespace):
    target_tsg = args.tsg_id
    if args.tenant:
        tenants = client.list_tenants()
        for t in tenants:
            if t.get("display_name", "").lower() == args.tenant.lower():
                target_tsg = str(t.get("id"))
                break

    with console.status("[bold green]Fetching Tenant UEs from Prisma Access 5G..."):
        res = client.list_tenant_ues(
            tsg_id=target_tsg,
            page=args.page,
            size=args.size,
            filter_query=args.filter_query,
        )

    if args.json:
        console.print_json(json.dumps(res, default=str))
        return

    items = res.get("data", [])
    total = res.get("totalItems", len(items))

    table = Table(title=f"Prisma Access 5G - Registered SIMs / Tenant UEs (Total: {total})")
    table.add_column("Tenant", style="bold blue")
    table.add_column("IMSI", style="bold green", no_wrap=True)
    table.add_column("IMEI", style="bold yellow", no_wrap=True)
    table.add_column("APN", style="magenta")
    table.add_column("Groups", style="cyan")
    table.add_column("Identity ID", style="dim", no_wrap=True)
    table.add_column("TSG ID", style="dim")

    for item in items:
        grp_str = ", ".join([g.get("group_name", "") for g in item.get("group", []) if g.get("group_name")])
        table.add_row(
            str(item.get("tenant_name") or item.get("tsg_id", "")),
            str(item.get("imsi", "")),
            str(item.get("imei", "")),
            str(item.get("apn", "")),
            grp_str or "None",
            str(item.get("identity_id") or item.get("id") or "N/A"),
            str(item.get("tsg_id", "")),
        )

    console.print(table)


def handle_get(client: Prisma5GClient, args: argparse.Namespace):
    with console.status(f"[bold green]Fetching details for UE {args.id}..."):
        res = client.get_tenant_ue(args.id)

    if args.json:
        console.print_json(json.dumps(res))
    else:
        console.print(Panel(json.dumps(res, indent=2), title=f"UE Details: {args.id}", expand=False))


def handle_add(client: Prisma5GClient, args: argparse.Namespace):
    target_tsg = args.tsg_id
    target_apn = args.apn or client.config.default_apn or "sasetest"
    if args.tenant:
        tenants = client.list_tenants()
        for t in tenants:
            if t.get("display_name", "").lower() == args.tenant.lower():
                target_tsg = str(t.get("id"))
                break

    # If no TSG ID provided and we have child tenants, auto-select or prompt
    if not target_tsg:
        tenants = client.list_tenants()
        children = [t for t in tenants if t.get("parent_id")]
        if len(children) == 1:
            target_tsg = str(children[0].get("id"))
        elif len(children) > 1:
            # Check if there is one called 'Transatel demo' or pick first child
            for c in children:
                if "transatel demo" in c.get("display_name", "").lower():
                    target_tsg = str(c.get("id"))
                    break
            if not target_tsg:
                target_tsg = str(children[0].get("id"))

    with console.status(f"[bold green]1/2 Registering SIM card mapping (IMSI: {args.imsi}, IMEI: {args.imei}, TSG: {target_tsg})..."):
        res = client.create_tenant_ue(
            imsi=args.imsi,
            imei=args.imei,
            apn=target_apn,
            tsg_id=target_tsg,
            root_tsg_id=args.root_tsg_id,
        )

    created_id = res.get("data", {}).get("id") or res.get("data", {}).get("identity_id")
    console.print(f"[bold green]✓ Successfully mapped SIM / Tenant UE![/bold green]")
    if created_id:
        console.print(f"  • [bold cyan]Identity ID:[/bold cyan] {created_id}")

    # If IP is provided, automatically trigger real-time 5G subscriber session registration
    if args.ipv4 or args.ipv6:
        session = UESession(
            imsi=args.imsi,
            imei=args.imei,
            apn=target_apn,
            ip_type=args.ip_type,
            ipv4_addr=args.ipv4,
            ipv6_addr=args.ipv6,
            msisdn=args.msisdn,
            slice_id=args.slice_id,
        )
        with console.status(f"[bold green]2/2 Activating real-time 5G session with IP {args.ipv4 or args.ipv6}..."):
            sess_res = client.register_ue_session(session)
        console.print(f"[bold green]✓ 5G Subscriber Session Activated (HTTP {sess_res.get('status_code', 202)})![/bold green]")
        console.print(f"  • [bold magenta]Allocated IP:[/bold magenta] {args.ipv4 or args.ipv6} ({args.ip_type})")

    console.print(Panel(json.dumps(res, indent=2, default=str), title="Response Data", expand=False))


def handle_update(client: Prisma5GClient, args: argparse.Namespace):
    with console.status(f"[bold green]Updating Tenant UE {args.id}..."):
        res = client.update_tenant_ue(
            identity_id=args.id,
            imsi=args.imsi,
            imei=args.imei,
            apn=args.apn,
            tsg_id=args.tsg_id,
        )
    console.print(f"[bold green]✓ Successfully updated UE {args.id}![/bold green]")
    console.print_json(json.dumps(res))

    # If group-id is provided, also update group membership
    if getattr(args, "group_id", None) is not None:
        gid = args.group_id.strip() if args.group_id else None
        if gid and gid.lower() in ("none", "null", ""):
            gid = None
        with console.status(f"[bold green]Updating group assignment to '{gid}'..."):
            g_res = client.assign_ue_to_group(ue_identity_id=args.id, target_group_id=gid, tsg_id=args.tsg_id)
        console.print(f"[bold green]✓ Group assignment updated![/bold green]")
        console.print_json(json.dumps(g_res))


def handle_delete(client: Prisma5GClient, args: argparse.Namespace):
    with console.status(f"[bold red]Deleting Tenant UE {args.id}..."):
        res = client.delete_tenant_ue(args.id)
    console.print(f"[bold green]✓ Successfully removed Tenant UE {args.id}![/bold green]")
    console.print_json(json.dumps(res))


def handle_bulk_delete(client: Prisma5GClient, args: argparse.Namespace):
    with console.status(f"[bold red]Bulk deleting {len(args.ids)} Tenant UEs..."):
        res = client.bulk_delete_tenant_ues(args.ids)
    console.print(f"[bold green]✓ Successfully deleted {len(args.ids)} UEs![/bold green]")
    console.print_json(json.dumps(res))


def handle_session_register(client: Prisma5GClient, args: argparse.Namespace):
    session = UESession(
        imsi=args.imsi,
        imei=args.imei,
        apn=args.apn,
        ip_type=args.ip_type,
        ipv4_addr=args.ipv4,
        ipv6_addr=args.ipv6,
        msisdn=args.msisdn,
        cell_id=args.cell_id,
        slice_id=args.slice_id,
    )
    with console.status("[bold green]Sending 5G UE session registration telemetry..."):
        res = client.register_ue_session(session)
    console.print(f"[bold green]✓ Subscriber session registration accepted (HTTP {res.get('status_code')})[/bold green]")
    console.print_json(json.dumps(res))


def handle_session_terminate(client: Prisma5GClient, args: argparse.Namespace):
    session = UESession(
        imsi=args.imsi,
        imei=args.imei,
        apn=args.apn,
        ip_type=args.ip_type,
        ipv4_addr=args.ipv4,
    )
    with console.status("[bold yellow]Sending 5G UE session termination telemetry..."):
        res = client.deregister_ue_session(session)
    console.print(f"[bold green]✓ Subscriber session termination accepted (HTTP {res.get('status_code')})[/bold green]")
    console.print_json(json.dumps(res))


def handle_groups(client: Prisma5GClient, args: argparse.Namespace):
    with console.status("[bold green]Fetching 5G subscriber user groups..."):
        res = client.list_user_groups(tsg_id=args.tsg_id, group_id=args.group_id)

    models = res.get("models", [])
    if args.json:
        console.print_json(json.dumps([{"group_id": g.group_id, "name": g.name, "user_count": g.user_count, "tsg_id": g.tsg_id, "tenant_name": g.tenant_name} for g in models]))
        return

    table = Table(title=f"5G Subscriber Groups (Count: {len(models)})")
    table.add_column("Tenant", style="bold blue")
    table.add_column("Group Name", style="bold green")
    table.add_column("Users", style="bold yellow")
    table.add_column("Group ID", style="cyan")
    table.add_column("TSG ID", style="dim")

    for g in models:
        table.add_row(
            str(g.tenant_name or g.tsg_id or ""),
            str(g.name or "N/A"),
            str(g.user_count if g.user_count is not None else "0"),
            str(g.group_id or "N/A"),
            str(g.tsg_id or ""),
        )

    console.print(table)


def handle_group_create(client: Prisma5GClient, args: argparse.Namespace):
    with console.status(f"[bold green]Creating subscriber group '{args.name}'..."):
        res = client.create_user_group(
            group_name=args.name,
            tsg_id=args.tsg_id,
            identity_ids=args.identities or [],
        )
    console.print(f"[bold green]✓ Successfully created Subscriber Group '{args.name}'![/bold green]")
    console.print_json(json.dumps(res))


def handle_group_get(client: Prisma5GClient, args: argparse.Namespace):
    with console.status(f"[bold green]Fetching group details for '{args.id}'..."):
        res = client.get_user_group(args.id)
    if args.json:
        console.print_json(json.dumps(res))
    else:
        console.print(Panel(json.dumps(res, indent=2), title=f"Group Details: {args.id}", expand=False))


PROTECTED_SYSTEM_GROUPS = {
    "6c73c05b-9977-4bed-a61c-30edc47a49f8",  # Restrictive
    "f7edf2ca-75ba-49b6-b02f-ab76516fb1d9",  # Permissive
}
PROTECTED_SYSTEM_GROUP_NAMES = {"restrictive", "permissive"}


def handle_group_delete(client: Prisma5GClient, args: argparse.Namespace):
    if str(args.id) in PROTECTED_SYSTEM_GROUPS:
        console.print("[bold red]Action Denied:[/bold red] 'Restrictive' and 'Permissive' are protected system groups and cannot be deleted.")
        sys.exit(1)
    try:
        g_info = client.get_user_group(args.id)
        d_arr = g_info.get("data", [])
        g_obj = d_arr[0] if d_arr and isinstance(d_arr, list) else g_info.get("data", {})
        g_name = (g_obj.get("group_name") or g_obj.get("name") or "").lower()
        if g_name in PROTECTED_SYSTEM_GROUP_NAMES:
            console.print(f"[bold red]Action Denied:[/bold red] System group '{g_name}' is protected and cannot be deleted.")
            sys.exit(1)
    except Exception:
        pass

    with console.status(f"[bold red]Deleting subscriber group '{args.id}'..."):
        res = client.delete_user_group(args.id)
    console.print(f"[bold green]✓ Successfully deleted Subscriber Group '{args.id}'![/bold green]")
    console.print_json(json.dumps(res))


def handle_assign_group(client: Prisma5GClient, args: argparse.Namespace):
    target_gid = args.group_id
    if not target_gid and args.group_name:
        # Search by group name
        groups = client.list_user_groups(tsg_id=args.tsg_id).get("models", [])
        for g in groups:
            if g.name and g.name.lower() == args.group_name.lower():
                target_gid = g.group_id
                break
        if not target_gid:
            console.print(f"[bold red]Error:[/bold red] Could not find group named '{args.group_name}'")
            sys.exit(1)

    if target_gid and target_gid.lower() in ("none", "null", ""):
        target_gid = None

    with console.status(f"[bold green]Assigning UE '{args.ue_id}' to group '{target_gid or 'None'}'..."):
        res = client.assign_ue_to_group(
            ue_identity_id=args.ue_id,
            target_group_id=target_gid,
            tsg_id=args.tsg_id,
        )
    console.print(f"[bold green]✓ UE Group assignment updated successfully![/bold green]")
    console.print_json(json.dumps(res))


def handle_summary(client: Prisma5GClient, args: argparse.Namespace):
    with console.status("[bold green]Querying 5G SASE Summary & Interconnects..."):
        summary = client.get_monitoring_summary(args.tsg_id)

    if args.json:
        console.print_json(data=summary)
        return

    # SCM-Style KPI Panels
    kpi_table = Table(show_header=True, header_style="bold cyan", title="5G SASE Summary (Strata Cloud Manager)")
    kpi_table.add_column("Total 5G Tenants", justify="center", style="bold green")
    kpi_table.add_column("Total Bandwidth (Mbps)", justify="center", style="bold magenta")
    kpi_table.add_column("Configured Users", justify="center", style="bold yellow")
    kpi_table.add_column("5G Interconnects", justify="center", style="bold cyan")
    kpi_table.add_column("Compute Region", justify="center", style="white")

    ic_status = f"{summary['interconnects_count']} ([green]{summary['interconnects_up']} Up[/green] / [red]{summary['interconnects_down']} Down[/red])"
    kpi_table.add_row(
        str(summary["total_5g_tenants"]),
        str(summary["total_bandwidth_mbps"]),
        str(summary["total_configured_users"]),
        ic_status,
        str(summary["compute_region"]),
    )
    console.print(kpi_table)


def handle_interconnect(client: Prisma5GClient, args: argparse.Namespace):
    with console.status("[bold green]Querying 5G Interconnect details..."):
        items = client.get_interconnect_details(args.tsg_id)

    if args.json:
        console.print_json(data=items)
        return

    table = Table(title=f"5G Regional Interconnects (Count: {len(items)})")
    table.add_column("Compute Region", style="bold cyan")
    table.add_column("Bandwidth", style="magenta")
    table.add_column("Status", style="bold green")
    table.add_column("VLAN Attachments", justify="center")
    table.add_column("VLAN Up", style="green", justify="center")
    table.add_column("VLAN Down", style="red", justify="center")

    for ic in items:
        status_entry = ic.get("vlanAttachmentStatusEntry", {})
        table.add_row(
            str(ic.get("computeRegion", "N/A")),
            f"{ic.get('bandwidth', 0)} Mbps",
            str(ic.get("status", "N/A")),
            str(ic.get("vlanAttachmentCount", 0)),
            str(status_entry.get("up", 0)),
            str(status_entry.get("down", 0)),
        )

    console.print(table)


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        config = load_config(args.env_file)
        client = Prisma5GClient(config)

        handlers = {
            "tenants": handle_tenants,
            "list": handle_list,
            "get": handle_get,
            "add": handle_add,
            "update": handle_update,
            "delete": handle_delete,
            "bulk-delete": handle_bulk_delete,
            "session-register": handle_session_register,
            "session-terminate": handle_session_terminate,
            "groups": handle_groups,
            "group-create": handle_group_create,
            "group-get": handle_group_get,
            "group-delete": handle_group_delete,
            "assign-group": handle_assign_group,
            "summary": handle_summary,
            "interconnect": handle_interconnect,
        }

        handler = handlers.get(args.command)
        if handler:
            handler(client, args)
        else:
            parser.print_help()
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        if args.debug:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
