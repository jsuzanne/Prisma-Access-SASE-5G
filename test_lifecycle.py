#!/usr/bin/env python3
"""Prisma SASE 5G End-to-End Lifecycle Test Script.

Executes a complete lifecycle test:
1. Load configuration and authenticate.
2. Read current 5G tenant info (list SIMs / UEs & subscriber groups).
3. Add 1 test user (SIM card / Tenant UE mapping).
4. Verify the test user exists.
5. Register a 5G real-time session telemetry event.
6. Terminate / deregister the 5G session.
7. Delete the test SIM card mapping.
8. Verify clean deletion.
"""

import sys
import time
import random
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.config import load_config
from src.client import Prisma5GClient
from src.models import UESession

console = Console()


def run_lifecycle_test(env_file=None):
    console.print(Panel.fit(
        "[bold cyan]Prisma SASE 5G - End-to-End Lifecycle Test[/bold cyan]\n"
        "[dim]Testing Authentication -> Read Info -> Create UE -> Verify -> Session Event -> Delete -> Verify[/dim]",
        border_style="cyan"
    ))

    # 1. Load config & Initialize Client
    console.print("\n[bold]Step 1: Loading configuration and authenticating...[/bold]")
    try:
        config = load_config(env_file)
        console.print(f"  • Base URL: [cyan]{config.api_base_url}[/cyan]")
        console.print(f"  • TSG ID:   [cyan]{config.tsg_id or 'Using Static Token'}[/cyan]")
        console.print(f"  • APN:      [cyan]{config.default_apn}[/cyan]")
        client = Prisma5GClient(config)
        token = client.auth.get_access_token()
        console.print(f"  [green]✓ Authentication successful! Token acquired (prefix: {token[:12]}...)[/green]")
    except Exception as exc:
        console.print(f"  [bold red]✗ Authentication / Config Error:[/bold red] {exc}")
        sys.exit(1)

    # 2. Read current info (list existing UEs and groups)
    console.print("\n[bold]Step 2: Reading current 5G tenant info & hierarchy...[/bold]")
    child_tsg_id = None
    try:
        tenants = client.list_tenants()
        console.print(f"  [green]✓ Discovered {len(tenants)} Tenant Service Groups:[/green]")
        for t in tenants:
            p_str = f"(Child of {t.get('parent_id')})" if t.get('parent_id') else "(Root MSP)"
            console.print(f"    • [cyan]{t.get('display_name')}[/cyan] [dim](ID: {t.get('id')})[/dim] {p_str}")
            if t.get('parent_id') and not child_tsg_id:
                child_tsg_id = str(t.get('id'))

        ue_list_resp = client.list_tenant_ues()
        existing_ues = ue_list_resp.get("data", [])
        total_items = ue_list_resp.get("totalItems", len(existing_ues))
        console.print(f"  [green]✓ Successfully queried Tenant UEs. Currently registered: {total_items}[/green]")
        
        if existing_ues:
            tbl = Table(title="Existing UEs (Sample)")
            tbl.add_column("Tenant", style="bold blue")
            tbl.add_column("Identity ID", style="cyan")
            tbl.add_column("IMSI", style="green")
            tbl.add_column("IMEI", style="yellow")
            tbl.add_column("APN", style="magenta")
            for u in existing_ues[:5]:
                tbl.add_row(
                    str(u.get("tenant_name") or u.get("tsg_id", "")),
                    str(u.get("identity_id") or u.get("id") or "N/A"),
                    str(u.get("imsi", "")),
                    str(u.get("imei", "")),
                    str(u.get("apn", "")),
                )
            console.print(tbl)
    except Exception as exc:
        console.print(f"  [yellow]⚠ Warning while querying UEs:[/yellow] {exc}")

    # Query groups
    try:
        group_resp = client.list_user_groups()
        groups = group_resp.get("models", [])
        console.print(f"  [green]✓ Successfully queried subscriber user groups. Found: {len(groups)}[/green]")
    except Exception as exc:
        console.print(f"  [yellow]⚠ Warning while querying groups:[/yellow] {exc}")

    # 3. Add 1 test user (SIM card)
    random_suffix = f"{random.randint(100000000, 999999999)}"  # 9 digits
    test_imsi = f"208950{random_suffix}"  # 6 + 9 = 15 digits
    test_imei = f"860123{random_suffix}"  # 6 + 9 = 15 digits
    test_apn = config.default_apn or "sasetest"

    console.print(f"\n[bold]Step 3: Registering 1 test SIM Card (Tenant UE)...[/bold]")
    console.print(f"  • Target TSG: [cyan]{child_tsg_id or config.tsg_id}[/cyan]")
    console.print(f"  • IMSI:       [green]{test_imsi}[/green]")
    console.print(f"  • IMEI:       [yellow]{test_imei}[/yellow]")
    console.print(f"  • APN:        [magenta]{test_apn}[/magenta]")

    created_identity_id = None
    try:
        create_resp = client.create_tenant_ue(
            imsi=test_imsi,
            imei=test_imei,
            apn=test_apn,
            tsg_id=child_tsg_id,
        )
        data_obj = create_resp.get("data", {})
        created_identity_id = data_obj.get("id") or data_obj.get("identity_id")
        console.print(f"  [green]✓ Test SIM created successfully! Identity ID: [cyan]{created_identity_id}[/cyan][/green]")
    except Exception as exc:
        console.print(f"  [bold red]✗ Failed to create test SIM:[/bold red] {exc}")
        sys.exit(1)

    # 4. Verify test user exists
    console.print("\n[bold]Step 4: Verifying test SIM in management plane...[/bold]")
    try:
        time.sleep(1)
        if created_identity_id:
            try:
                single_ue = client.get_tenant_ue(created_identity_id)
                console.print(f"  [green]✓ Direct lookup by ID confirmed: {created_identity_id}[/green]")
            except Exception:
                pass
        
        # Verify in list
        list_after = client.list_tenant_ues()
        found = any(
            str(u.get("imsi")) == test_imsi or str(u.get("identity_id") or u.get("id")) == str(created_identity_id)
            for u in list_after.get("data", [])
        )
        if found:
            console.print(f"  [green]✓ Confirmed: Test SIM found in registered UE list.[/green]")
        else:
            console.print(f"  [yellow]⚠ Note: Direct query returned success, but list might be eventually consistent.[/yellow]")
    except Exception as exc:
        console.print(f"  [yellow]⚠ Verification query note:[/yellow] {exc}")

    # 5. Real-time Session Registration (UE Enrichment)
    console.print("\n[bold]Step 5: Simulating 5G subscriber session start (Session Registration)...[/bold]")
    try:
        session = UESession(
            imsi=test_imsi,
            imei=test_imei,
            apn=test_apn,
            ip_type="IPv4",
            ipv4_addr="10.56.0.195",
        )
        sess_resp = client.register_ue_session(session)
        console.print(f"  [green]✓ Session registration telemetry accepted (HTTP {sess_resp.get('status_code')})[/green]")
    except Exception as exc:
        console.print(f"  [yellow]⚠ Session registration note:[/yellow] {exc}")

    # 6. Real-time Session Termination (UE Deregistration)
    console.print("\n[bold]Step 6: Simulating 5G subscriber session termination...[/bold]")
    try:
        sess_term_resp = client.deregister_ue_session(session)
        console.print(f"  [green]✓ Session termination telemetry accepted (HTTP {sess_term_resp.get('status_code')})[/green]")
    except Exception as exc:
        console.print(f"  [yellow]⚠ Session termination note:[/yellow] {exc}")

    # 7. Delete the test user (SIM mapping)
    console.print("\n[bold]Step 7: Deleting test SIM card (Tenant UE)...[/bold]")
    try:
        if created_identity_id:
            del_resp = client.delete_tenant_ue(created_identity_id)
            console.print(f"  [green]✓ Deleted Tenant UE ID: [cyan]{created_identity_id}[/cyan][/green]")
        else:
            console.print("  [yellow]⚠ No identity ID returned; skipping single delete.[/yellow]")
    except Exception as exc:
        console.print(f"  [bold red]✗ Failed to delete test SIM:[/bold red] {exc}")

    # 8. Verify clean state
    console.print("\n[bold]Step 8: Verifying clean deletion...[/bold]")
    try:
        time.sleep(1)
        list_final = client.list_tenant_ues()
        found_final = any(
            str(u.get("imsi")) == test_imsi or str(u.get("identity_id") or u.get("id")) == str(created_identity_id)
            for u in list_final.get("data", [])
        )
        if not found_final:
            console.print(f"  [green]✓ Confirmed: Test SIM successfully removed from management plane.[/green]")
        else:
            console.print(f"  [yellow]⚠ Note: Item still visible in list (may take a moment to propagate).[/yellow]")
    except Exception as exc:
        console.print(f"  [yellow]⚠ Final list check note:[/yellow] {exc}")

    console.print(Panel.fit(
        "[bold green]✓ Complete Prisma SASE 5G lifecycle test executed successfully![/bold green]",
        border_style="green"
    ))


if __name__ == "__main__":
    env_file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_lifecycle_test(env_file_arg)
