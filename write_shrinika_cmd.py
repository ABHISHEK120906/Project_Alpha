"""
Helper: writes the create_shrinika_demo management command.
Run: python write_shrinika_cmd.py
"""
import os

TARGET = os.path.join(
    os.path.dirname(__file__),
    "core", "management", "commands", "create_shrinika_demo.py"
)

CMD = '''\
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from core.models import (
    Client, Project, Payment, Task, Note, ActivityLog,
    UserProfile, Income, Expense, Invoice, InvoiceItem,
    Notification, CalendarEvent,
)
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = "Creates Shrinika demo user with comprehensive realistic freelancer data."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Setting up Shrinika demo account..."))

        user, created = User.objects.get_or_create(
            username="Shrinika",
            defaults={
                "email": "shrinika@freelancetrack.demo",
                "first_name": "Shrinika",
                "last_name": "Desai",
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
        )
        user.set_password("Team@123456")
        user.email = "shrinika@freelancetrack.demo"
        user.first_name = "Shrinika"
        user.last_name = "Desai"
        user.save()
        verb = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{verb} user: Shrinika / Team@123456"))

        _seed(user, self)


def _seed(user, cmd):
    today = timezone.now().date()

    # ── UserProfile ──────────────────────────────────────────────────────────
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.role = "user"
    profile.is_verified = True
    profile.phone_number = "+91 98765 43210"
    profile.address = "204, Silver Oak Apartments, Baner, Pune, Maharashtra 411045"
    profile.bio = (
        "Full-Stack Freelance Developer and UI/UX Designer with 5+ years of experience. "
        "Specializing in Python (Django/FastAPI), React, Flutter, and scalable SaaS products "
        "for startups and enterprises across India, UAE, and the US."
    )
    profile.skills = (
        "Python, Django, FastAPI, React, Next.js, Flutter, PostgreSQL, MySQL, "
        "Redis, Docker, AWS, Figma, TailwindCSS, REST API, GraphQL"
    )
    profile.experience = "5+ years building production-grade web and mobile applications"
    profile.portfolio_website = "https://shrinika.dev"
    profile.social_github = "https://github.com/shrinika-desai"
    profile.social_linkedin = "https://linkedin.com/in/shrinika-desai"
    profile.social_twitter = "https://twitter.com/shrinika_codes"
    profile.save()

    # ── Clients ──────────────────────────────────────────────────────────────
    clients_raw = [
        dict(name="Rahul Mehta", email="rahul.mehta@techvista.in", phone="+91 98201 11234",
             company="TechVista Solutions Pvt. Ltd.",
             address="12th Floor, Cyber City, DLF Phase 2, Gurgaon, HR 122002",
             status="active", notes="Long-term enterprise client. Monthly retainer."),
        dict(name="Priya Kapoor", email="priya@bloomify.co", phone="+91 70210 88765",
             company="Bloomify E-Commerce",
             address="Unit 5, BKC Bandra East, Mumbai, MH 400051",
             status="active", notes="Fashion e-commerce startup. Very design-conscious."),
        dict(name="Arjun Nair", email="arjun.nair@finedgetech.io", phone="+91 91010 55432",
             company="FinEdge Technologies",
             address="No. 42, Whitefield Main Rd, Bangalore, KA 560066",
             status="active", notes="Fintech startup. Strict data security. Net-30 payment."),
        dict(name="Sneha Joshi", email="sneha@healthnestapp.com", phone="+91 88005 67890",
             company="HealthNest Digital",
             address="3rd Floor, SB Road, Shivajinagar, Pune, MH 411005",
             status="active", notes="Healthcare SaaS. Weekly standups on Friday 4 PM."),
        dict(name="Mohammed Al-Rashid", email="m.alrashid@dubaitechgroup.ae",
             phone="+971 50 123 4567", company="Dubai Tech Group LLC",
             address="Office 802, Emaar Square, Downtown Dubai, UAE",
             status="active", notes="UAE-based enterprise. USD billing preferred."),
        dict(name="Kavya Sharma", email="kavya@edusparks.in", phone="+91 82010 33456",
             company="EduSparks Learning",
             address="Plot 11, Sector 18, Noida, UP 201301",
             status="active", notes="EdTech startup. Advance payment preferred."),
        dict(name="Vikram Patil", email="vikram@realestatehub.co.in", phone="+91 99501 22100",
             company="RealEstateHub India",
             address="7, Senapati Bapat Marg, Lower Parel, Mumbai, MH 400013",
             status="active", notes="Real estate portal. Milestone-based payment."),
        dict(name="Aisha Patel", email="aisha.patel@brandcraft.studio", phone="+91 76500 11987",
             company="BrandCraft Studio",
             address="Studio 3, Law Garden Road, Navrangpura, Ahmedabad, GJ 380009",
             status="active", notes="Creative agency. Retainer model. Portfolio-worthy work."),
        dict(name="James Carter", email="james.carter@nexusapp.us", phone="+1 (415) 987-6543",
             company="Nexus App Inc.",
             address="555 Market St, Suite 200, San Francisco, CA 94105, USA",
             status="active", notes="US-based SaaS startup. USD billing. Async comms."),
        dict(name="Divya Menon", email="divya@logisync.in", phone="+91 94450 78321",
             company="LogiSync Technologies",
             address="Smart Works, Indiranagar, Bangalore, KA 560038",
             status="active", notes="Logistics SaaS. Complex dashboard requirements."),
        dict(name="Rohan Desai", email="rohan.desai@cloudpulse.io", phone="+91 87090 44560",
             company="CloudPulse Analytics",
             address="WeWork, Baner Rd, Baner, Pune, MH 411045",
             status="inactive", notes="Project on hold. Potential reactivation Q1 2027."),
        dict(name="Tanvi Kulkarni", email="tanvi@styloai.fashion", phone="+91 99660 23456",
             company="StyloAI Fashion",
             address="Floor 4, Prestige Tower, MG Road, Bengaluru, KA 560001",
             status="prospective", notes="AI fashion startup. Proposal sent. Discovery call scheduled."),
    ]

    clients = {}
    for c in clients_raw:
        name = c.pop("name")
        obj, _ = Client.objects.get_or_create(user=user, name=name, defaults=c)
        clients[name] = obj
    cmd.stdout.write(cmd.style.SUCCESS(f"{len(clients)} clients created"))

    # ── Projects ─────────────────────────────────────────────────────────────
    projects_raw = [
        dict(name="TechVista Enterprise ERP Portal",
             client=clients["Rahul Mehta"],
             description="Full-featured ERP with Django + React, RBAC, PostgreSQL, Redis, AWS.",
             status="in_progress", priority="high",
             budget=Decimal("185000.00"), progress=68,
             start_date=today - timedelta(days=60), deadline=today + timedelta(days=30)),
        dict(name="Bloomify Mobile App iOS and Android",
             client=clients["Priya Kapoor"],
             description="Flutter cross-platform app with AR try-on, wishlist, cart, Razorpay.",
             status="in_progress", priority="urgent",
             budget=Decimal("120000.00"), progress=52,
             start_date=today - timedelta(days=35), deadline=today + timedelta(days=20)),
        dict(name="FinEdge Trading Dashboard",
             client=clients["Arjun Nair"],
             description="Real-time trading dashboard with WebSocket, Chart.js, FastAPI backend.",
             status="in_progress", priority="urgent",
             budget=Decimal("95000.00"), progress=40,
             start_date=today - timedelta(days=20), deadline=today + timedelta(days=25)),
        dict(name="HealthNest Patient Portal",
             client=clients["Sneha Joshi"],
             description="Patient management portal with appointments, teleconsultation, prescriptions.",
             status="in_progress", priority="high",
             budget=Decimal("140000.00"), progress=35,
             start_date=today - timedelta(days=18), deadline=today + timedelta(days=45)),
        dict(name="Dubai Tech Group Smart City Dashboard",
             client=clients["Mohammed Al-Rashid"],
             description="Enterprise IoT Smart City dashboard with English/Arabic support.",
             status="completed", priority="urgent",
             budget=Decimal("320000.00"), progress=100,
             start_date=today - timedelta(days=120), deadline=today - timedelta(days=15)),
        dict(name="EduSparks Learning Management System",
             client=clients["Kavya Sharma"],
             description="Complete LMS with live classes, quiz engine, gamification, parent dashboard.",
             status="completed", priority="high",
             budget=Decimal("88000.00"), progress=100,
             start_date=today - timedelta(days=90), deadline=today - timedelta(days=20)),
        dict(name="RealEstateHub Property Listing Portal",
             client=clients["Vikram Patil"],
             description="Property marketplace with Google Maps, virtual tours, EMI calculator.",
             status="in_progress", priority="medium",
             budget=Decimal("75000.00"), progress=60,
             start_date=today - timedelta(days=45), deadline=today + timedelta(days=15)),
        dict(name="BrandCraft Client Portfolio and CMS",
             client=clients["Aisha Patel"],
             description="Headless CMS with drag-drop builder, case studies, lead capture.",
             status="completed", priority="medium",
             budget=Decimal("42000.00"), progress=100,
             start_date=today - timedelta(days=70), deadline=today - timedelta(days=30)),
        dict(name="Nexus App SaaS Analytics Platform",
             client=clients["James Carter"],
             description="B2B SaaS with multi-tenant architecture, custom reports, Stripe billing.",
             status="in_progress", priority="high",
             budget=Decimal("210000.00"), progress=25,
             start_date=today - timedelta(days=10), deadline=today + timedelta(days=60)),
        dict(name="LogiSync Fleet Management System",
             client=clients["Divya Menon"],
             description="GPS fleet tracking with route optimization and fuel analytics.",
             status="on_hold", priority="medium",
             budget=Decimal("65000.00"), progress=20,
             start_date=today - timedelta(days=40), deadline=today + timedelta(days=50)),
        dict(name="TechVista HR and Payroll Module",
             client=clients["Rahul Mehta"],
             description="ERP add-on: employee onboarding, leave, attendance, salary slips.",
             status="pending", priority="medium",
             budget=Decimal("55000.00"), progress=0,
             start_date=today + timedelta(days=5), deadline=today + timedelta(days=60)),
        dict(name="Bloomify Brand Identity and Design System",
             client=clients["Priya Kapoor"],
             description="Logo, color palette, typography, Figma components, brand guidelines.",
             status="completed", priority="low",
             budget=Decimal("25000.00"), progress=100,
             start_date=today - timedelta(days=55), deadline=today - timedelta(days=25)),
        dict(name="FinEdge Compliance and Audit Report Tool",
             client=clients["Arjun Nair"],
             description="Automated SEBI compliance checker and PDF audit report generator.",
             status="pending", priority="high",
             budget=Decimal("45000.00"), progress=0,
             start_date=today + timedelta(days=10), deadline=today + timedelta(days=55)),
    ]

    projects = {}
    for p in projects_raw:
        name = p.pop("name")
        obj, _ = Project.objects.get_or_create(user=user, name=name, defaults=p)
        projects[name] = obj
    cmd.stdout.write(cmd.style.SUCCESS(f"{len(projects)} projects created"))

    # ── Tasks ────────────────────────────────────────────────────────────────
    tasks_raw = [
        dict(title="Setup Django multi-app project structure", proj="TechVista Enterprise ERP Portal", status="completed", priority="high", due=today - timedelta(days=55), est=Decimal("8"), act=Decimal("7.5")),
        dict(title="Design DB schema for HR and Inventory modules", proj="TechVista Enterprise ERP Portal", status="completed", priority="high", due=today - timedelta(days=45), est=Decimal("12"), act=Decimal("14")),
        dict(title="Build Role-Based Access Control system", proj="TechVista Enterprise ERP Portal", status="completed", priority="urgent", due=today - timedelta(days=30), est=Decimal("16"), act=Decimal("18")),
        dict(title="Implement Finance module Ledger and P&L", proj="TechVista Enterprise ERP Portal", status="in_progress", priority="high", due=today + timedelta(days=8), est=Decimal("20"), act=Decimal("10")),
        dict(title="React dashboard UI with sidebar navigation", proj="TechVista Enterprise ERP Portal", status="in_progress", priority="medium", due=today + timedelta(days=15), est=Decimal("24"), act=Decimal("8")),
        dict(title="Write integration tests for all API endpoints", proj="TechVista Enterprise ERP Portal", status="todo", priority="medium", due=today + timedelta(days=25), est=Decimal("16"), act=None),
        dict(title="Setup Flutter project with Riverpod state management", proj="Bloomify Mobile App iOS and Android", status="completed", priority="high", due=today - timedelta(days=30), est=Decimal("6"), act=Decimal("5")),
        dict(title="Product listing and search screen", proj="Bloomify Mobile App iOS and Android", status="completed", priority="high", due=today - timedelta(days=20), est=Decimal("18"), act=Decimal("20")),
        dict(title="AR try-on feature integration ARCore ARKit", proj="Bloomify Mobile App iOS and Android", status="in_progress", priority="urgent", due=today + timedelta(days=5), est=Decimal("30"), act=Decimal("15")),
        dict(title="Razorpay payment gateway integration", proj="Bloomify Mobile App iOS and Android", status="todo", priority="high", due=today + timedelta(days=12), est=Decimal("12"), act=None),
        dict(title="WebSocket live ticker feed implementation", proj="FinEdge Trading Dashboard", status="completed", priority="urgent", due=today - timedelta(days=10), est=Decimal("14"), act=Decimal("16")),
        dict(title="Portfolio P&L charts with Chart.js", proj="FinEdge Trading Dashboard", status="in_progress", priority="high", due=today + timedelta(days=7), est=Decimal("10"), act=Decimal("4")),
        dict(title="JWT auth and 2FA setup in FastAPI", proj="FinEdge Trading Dashboard", status="todo", priority="urgent", due=today + timedelta(days=3), est=Decimal("8"), act=None),
        dict(title="Patient appointment booking system", proj="HealthNest Patient Portal", status="in_progress", priority="high", due=today + timedelta(days=10), est=Decimal("20"), act=Decimal("8")),
        dict(title="Video consultation module WebRTC", proj="HealthNest Patient Portal", status="todo", priority="high", due=today + timedelta(days=25), est=Decimal("24"), act=None),
        dict(title="Google Maps property pin integration", proj="RealEstateHub Property Listing Portal", status="completed", priority="high", due=today - timedelta(days=10), est=Decimal("10"), act=Decimal("9")),
        dict(title="Advanced search filters price BHK area", proj="RealEstateHub Property Listing Portal", status="in_progress", priority="medium", due=today + timedelta(days=8), est=Decimal("8"), act=Decimal("4")),
        dict(title="Multi-tenant architecture setup", proj="Nexus App SaaS Analytics Platform", status="in_progress", priority="urgent", due=today + timedelta(days=7), est=Decimal("20"), act=Decimal("10")),
        dict(title="Stripe subscription billing integration", proj="Nexus App SaaS Analytics Platform", status="todo", priority="high", due=today + timedelta(days=20), est=Decimal("12"), act=None),
    ]

    tc = 0
    for t in tasks_raw:
        p = projects.get(t["proj"])
        if p:
            _, c2 = Task.objects.get_or_create(
                user=user, title=t["title"], project=p,
                defaults=dict(status=t["status"], priority=t["priority"],
                              due_date=t["due"], estimated_hours=t["est"], actual_hours=t["act"]),
            )
            if c2:
                tc += 1
    cmd.stdout.write(cmd.style.SUCCESS(f"{tc} tasks created"))

    # ── Payments ─────────────────────────────────────────────────────────────
    payments_raw = [
        dict(proj="Dubai Tech Group Smart City Dashboard", amount=Decimal("106667.00"), status="paid", method="bank_transfer", due=today - timedelta(days=110), paid=today - timedelta(days=108), inv="INV-SHR-2025-001", desc="Milestone 1 - Project Kickoff 33%"),
        dict(proj="Dubai Tech Group Smart City Dashboard", amount=Decimal("106667.00"), status="paid", method="bank_transfer", due=today - timedelta(days=80), paid=today - timedelta(days=78), inv="INV-SHR-2025-002", desc="Milestone 2 - Core Dashboard 33%"),
        dict(proj="Dubai Tech Group Smart City Dashboard", amount=Decimal("106666.00"), status="paid", method="bank_transfer", due=today - timedelta(days=20), paid=today - timedelta(days=18), inv="INV-SHR-2025-003", desc="Final Payment - Deployment 34%"),
        dict(proj="EduSparks Learning Management System", amount=Decimal("44000.00"), status="paid", method="bank_transfer", due=today - timedelta(days=80), paid=today - timedelta(days=78), inv="INV-SHR-2025-004", desc="Milestone 1 - LMS Core 50%"),
        dict(proj="EduSparks Learning Management System", amount=Decimal("44000.00"), status="paid", method="bank_transfer", due=today - timedelta(days=25), paid=today - timedelta(days=22), inv="INV-SHR-2025-005", desc="Final Payment - Gamification 50%"),
        dict(proj="Bloomify Brand Identity and Design System", amount=Decimal("12500.00"), status="paid", method="bank_transfer", due=today - timedelta(days=50), paid=today - timedelta(days=49), inv="INV-SHR-2025-006", desc="Advance 50% Brand Identity"),
        dict(proj="Bloomify Brand Identity and Design System", amount=Decimal("12500.00"), status="paid", method="bank_transfer", due=today - timedelta(days=26), paid=today - timedelta(days=24), inv="INV-SHR-2025-007", desc="Final 50% Design System"),
        dict(proj="BrandCraft Client Portfolio and CMS", amount=Decimal("21000.00"), status="paid", method="bank_transfer", due=today - timedelta(days=60), paid=today - timedelta(days=59), inv="INV-SHR-2025-008", desc="Advance 50% CMS Portfolio"),
        dict(proj="BrandCraft Client Portfolio and CMS", amount=Decimal("21000.00"), status="paid", method="bank_transfer", due=today - timedelta(days=31), paid=today - timedelta(days=29), inv="INV-SHR-2025-009", desc="Final 50% CMS Portfolio"),
        dict(proj="TechVista Enterprise ERP Portal", amount=Decimal("55500.00"), status="paid", method="bank_transfer", due=today - timedelta(days=55), paid=today - timedelta(days=53), inv="INV-SHR-2026-001", desc="Advance 30% ERP Kickoff"),
        dict(proj="TechVista Enterprise ERP Portal", amount=Decimal("74000.00"), status="paid", method="bank_transfer", due=today - timedelta(days=20), paid=today - timedelta(days=18), inv="INV-SHR-2026-002", desc="Milestone 2 - 40% Phase"),
        dict(proj="TechVista Enterprise ERP Portal", amount=Decimal("55500.00"), status="pending", method="bank_transfer", due=today + timedelta(days=30), paid=None, inv="INV-SHR-2026-003", desc="Final 30% ERP Delivery"),
        dict(proj="Bloomify Mobile App iOS and Android", amount=Decimal("48000.00"), status="paid", method="bank_transfer", due=today - timedelta(days=30), paid=today - timedelta(days=28), inv="INV-SHR-2026-004", desc="Advance 40% Flutter App"),
        dict(proj="Bloomify Mobile App iOS and Android", amount=Decimal("72000.00"), status="pending", method="bank_transfer", due=today + timedelta(days=20), paid=None, inv="INV-SHR-2026-005", desc="Remaining 60% Mobile App"),
        dict(proj="FinEdge Trading Dashboard", amount=Decimal("47500.00"), status="paid", method="bank_transfer", due=today - timedelta(days=15), paid=today - timedelta(days=14), inv="INV-SHR-2026-006", desc="Advance 50% Trading Dashboard"),
        dict(proj="FinEdge Trading Dashboard", amount=Decimal("47500.00"), status="pending", method="bank_transfer", due=today + timedelta(days=25), paid=None, inv="INV-SHR-2026-007", desc="Final 50% Dashboard Delivery"),
        dict(proj="HealthNest Patient Portal", amount=Decimal("42000.00"), status="paid", method="bank_transfer", due=today - timedelta(days=14), paid=today - timedelta(days=13), inv="INV-SHR-2026-008", desc="Advance 30% Patient Portal"),
        dict(proj="HealthNest Patient Portal", amount=Decimal("98000.00"), status="pending", method="bank_transfer", due=today + timedelta(days=45), paid=None, inv="INV-SHR-2026-009", desc="Remaining 70% Portal Delivery"),
        dict(proj="RealEstateHub Property Listing Portal", amount=Decimal("37500.00"), status="paid", method="bank_transfer", due=today - timedelta(days=40), paid=today - timedelta(days=38), inv="INV-SHR-2026-010", desc="Advance 50% Property Portal"),
        dict(proj="RealEstateHub Property Listing Portal", amount=Decimal("37500.00"), status="pending", method="bank_transfer", due=today + timedelta(days=15), paid=None, inv="INV-SHR-2026-011", desc="Final 50% Portal Delivery"),
        dict(proj="Nexus App SaaS Analytics Platform", amount=Decimal("63000.00"), status="paid", method="stripe", due=today - timedelta(days=8), paid=today - timedelta(days=7), inv="INV-SHR-2026-012", desc="Advance 30% SaaS Platform"),
        dict(proj="Nexus App SaaS Analytics Platform", amount=Decimal("147000.00"), status="pending", method="stripe", due=today + timedelta(days=60), paid=None, inv="INV-SHR-2026-013", desc="Remaining 70% SaaS Delivery"),
    ]

    pc = 0
    for pm in payments_raw:
        p = projects.get(pm["proj"])
        if p:
            _, c3 = Payment.objects.get_or_create(
                user=user, invoice_number=pm["inv"],
                defaults=dict(project=p, amount=pm["amount"], status=pm["status"],
                              payment_method=pm["method"], due_date=pm["due"],
                              paid_date=pm.get("paid"), description=pm.get("desc", "")),
            )
            if c3:
                pc += 1
    cmd.stdout.write(cmd.style.SUCCESS(f"{pc} payments created"))

    # ── Income ───────────────────────────────────────────────────────────────
    incomes_raw = [
        dict(title="Monthly Retainer TechVista Jul 2026", client=clients["Rahul Mehta"], project=projects["TechVista Enterprise ERP Portal"], amount=Decimal("25000.00"), category="retainer", date=today - timedelta(days=20)),
        dict(title="Monthly Retainer TechVista Aug 2026", client=clients["Rahul Mehta"], project=projects["TechVista Enterprise ERP Portal"], amount=Decimal("25000.00"), category="retainer", date=today - timedelta(days=2)),
        dict(title="Consulting HealthNest Product Strategy", client=clients["Sneha Joshi"], project=projects["HealthNest Patient Portal"], amount=Decimal("8500.00"), category="consulting", date=today - timedelta(days=12)),
        dict(title="Consulting FinEdge Security Audit", client=clients["Arjun Nair"], project=projects["FinEdge Trading Dashboard"], amount=Decimal("12000.00"), category="consulting", date=today - timedelta(days=8)),
        dict(title="Dubai Smart City Completion Bonus", client=clients["Mohammed Al-Rashid"], project=projects["Dubai Tech Group Smart City Dashboard"], amount=Decimal("15000.00"), category="project", date=today - timedelta(days=18)),
        dict(title="Royalty Bloomify Design System License", client=clients["Aisha Patel"], project=None, amount=Decimal("5500.00"), category="royalty", date=today - timedelta(days=5)),
        dict(title="Nexus SaaS Advance Payment USD", client=clients["James Carter"], project=projects["Nexus App SaaS Analytics Platform"], amount=Decimal("63000.00"), category="project", date=today - timedelta(days=7)),
    ]

    ic = 0
    for inc in incomes_raw:
        _, c4 = Income.objects.get_or_create(user=user, title=inc["title"], defaults=inc)
        if c4:
            ic += 1
    cmd.stdout.write(cmd.style.SUCCESS(f"{ic} income records created"))

    # ── Expenses ─────────────────────────────────────────────────────────────
    expenses_raw = [
        dict(title="Adobe Creative Cloud Annual License", amount=Decimal("6290.00"), category="software", date=today - timedelta(days=45)),
        dict(title="JetBrains All Products Pack", amount=Decimal("3800.00"), category="software", date=today - timedelta(days=40)),
        dict(title="AWS Cloud Services July 2026", amount=Decimal("4250.00"), category="software", date=today - timedelta(days=20)),
        dict(title="AWS Cloud Services Aug 2026", amount=Decimal("4800.00"), category="software", date=today - timedelta(days=2)),
        dict(title="Figma Organization Plan Quarterly", amount=Decimal("3150.00"), category="software", date=today - timedelta(days=30)),
        dict(title="Notion Team Plan Annual", amount=Decimal("1200.00"), category="software", date=today - timedelta(days=50)),
        dict(title="New MacBook Pro M3 16 inch", amount=Decimal("189000.00"), category="hardware", date=today - timedelta(days=60)),
        dict(title="LG 27 inch 4K Monitor", amount=Decimal("32000.00"), category="hardware", date=today - timedelta(days=55)),
        dict(title="Co-working Space 91Springboard Baner Aug", amount=Decimal("7500.00"), category="office", date=today - timedelta(days=3)),
        dict(title="Subcontractor Ankit React Dev 20 hrs", amount=Decimal("18000.00"), category="subcontractor", date=today - timedelta(days=15)),
        dict(title="Google Ads Campaign Portfolio", amount=Decimal("5000.00"), category="marketing", date=today - timedelta(days=25)),
        dict(title="LinkedIn Premium Career Plan", amount=Decimal("2400.00"), category="marketing", date=today - timedelta(days=35)),
        dict(title="CA Fees GST Filing Q1 2026", amount=Decimal("8500.00"), category="tax", date=today - timedelta(days=42)),
        dict(title="Travel Mumbai Client Visit Bloomify", amount=Decimal("4200.00"), category="travel", date=today - timedelta(days=28)),
    ]

    ec = 0
    for exp in expenses_raw:
        _, c5 = Expense.objects.get_or_create(user=user, title=exp["title"], defaults=exp)
        if c5:
            ec += 1
    cmd.stdout.write(cmd.style.SUCCESS(f"{ec} expenses created"))

    # ── Invoices ─────────────────────────────────────────────────────────────
    invoices_data = [
        dict(inv_no="INV-SHR-FORMAL-001",
             client=clients["Rahul Mehta"],
             project=projects["TechVista Enterprise ERP Portal"],
             issue=today - timedelta(days=10), due=today + timedelta(days=20),
             status="sent", sub=Decimal("55500"), tax_r=Decimal("18"),
             tax_a=Decimal("9990"), disc=Decimal("0"), total=Decimal("65490"),
             notes="Final milestone. GST 18%.",
             items=[("ERP Finance Module Development", Decimal("1"), Decimal("30000")),
                    ("RBAC User Management Module", Decimal("1"), Decimal("15000")),
                    ("React Dashboard UI", Decimal("1"), Decimal("10500"))]),
        dict(inv_no="INV-SHR-FORMAL-002",
             client=clients["Priya Kapoor"],
             project=projects["Bloomify Mobile App iOS and Android"],
             issue=today - timedelta(days=5), due=today + timedelta(days=25),
             status="sent", sub=Decimal("72000"), tax_r=Decimal("18"),
             tax_a=Decimal("12960"), disc=Decimal("5000"), total=Decimal("79960"),
             notes="Loyalty discount Rs.5000 applied.",
             items=[("Flutter Mobile App Development iOS Android", Decimal("1"), Decimal("50000")),
                    ("AR Try-On Feature Integration", Decimal("1"), Decimal("15000")),
                    ("Razorpay Payment Integration", Decimal("1"), Decimal("7000"))]),
        dict(inv_no="INV-SHR-FORMAL-003",
             client=clients["James Carter"],
             project=projects["Nexus App SaaS Analytics Platform"],
             issue=today - timedelta(days=7), due=today + timedelta(days=23),
             status="paid", sub=Decimal("63000"), tax_r=Decimal("0"),
             tax_a=Decimal("0"), disc=Decimal("0"), total=Decimal("63000"),
             notes="International client. No GST.",
             items=[("Multi-Tenant SaaS Architecture Setup", Decimal("1"), Decimal("35000")),
                    ("Stripe Subscription Billing Advance", Decimal("1"), Decimal("18000")),
                    ("Technical Consulting 10 hrs", Decimal("10"), Decimal("1000"))]),
    ]

    invc = 0
    for inv_d in invoices_data:
        items = inv_d.pop("items")
        inv_no = inv_d.pop("inv_no")
        inv_obj, c6 = Invoice.objects.get_or_create(
            user=user, invoice_number=inv_no,
            defaults=dict(client=inv_d["client"], project=inv_d["project"],
                          issue_date=inv_d["issue"], due_date=inv_d["due"],
                          status=inv_d["status"], subtotal=inv_d["sub"],
                          tax_rate=inv_d["tax_r"], tax_amount=inv_d["tax_a"],
                          discount_amount=inv_d["disc"], total=inv_d["total"],
                          notes=inv_d["notes"]),
        )
        if c6:
            for desc, qty, up in items:
                InvoiceItem.objects.create(invoice=inv_obj, description=desc,
                                           quantity=qty, unit_price=up, amount=qty * up)
            invc += 1
    cmd.stdout.write(cmd.style.SUCCESS(f"{invc} invoices created"))

    # ── Notes ────────────────────────────────────────────────────────────────
    notes_raw = [
        dict(title="TechVista Tech Stack Decisions", content="Backend: Django 5 + DRF. DB: PostgreSQL 16. Cache: Redis 7. Frontend: React 18 + Vite + TailwindCSS. Deploy: AWS ECS Docker. CI/CD: GitHub Actions.", project=projects["TechVista Enterprise ERP Portal"], client=None),
        dict(title="Bloomify App Design Requirements", content="Color: Soft pink #F8BBD0 + White + Deep Purple #4A148C. Typography: Playfair Display headings, Inter body. Luxury feel. Smooth animations.", project=projects["Bloomify Mobile App iOS and Android"], client=None),
        dict(title="FinEdge Security Compliance Notes", content="SEBI CSCRF compliance required. AES-256 encryption at rest, TLS 1.3 in transit. Audit logs for all financial transactions. Rate limit 50 req/min.", project=projects["FinEdge Trading Dashboard"], client=None),
        dict(title="Mohammed Al-Rashid Client Preferences", content="Formal email only. GST UTC+4. USD monthly billing. Friday email status updates. Requested referral letter after Smart City project.", project=None, client=clients["Mohammed Al-Rashid"]),
        dict(title="Revenue Goals FY 2026-27", content="Target Rs.30 Lakhs annual. Current pipeline Rs.18.5 Lakhs. Strategy: 2 retainer + 3 active project clients. Expand to Dubai and Singapore.", project=None, client=None),
        dict(title="AWS Cost Optimization Plan", content="Switch to Reserved Instances saves 35%. S3 Intelligent-Tiering for media. CloudFront for statics. Budget alert Rs.5000/month.", project=None, client=None),
        dict(title="StyloAI Proposal Notes", content="Budget Rs.60K MVP. Features: AI outfit recommendations, virtual wardrobe, social sharing. Timeline 3 months. Recommend Next.js + Python ML backend.", project=None, client=clients["Tanvi Kulkarni"]),
    ]

    nc = 0
    for n in notes_raw:
        if not Note.objects.filter(user=user, title=n["title"]).exists():
            Note.objects.create(user=user, title=n["title"], content=n["content"],
                                project=n.get("project"), client=n.get("client"))
            nc += 1
    cmd.stdout.write(cmd.style.SUCCESS(f"{nc} notes created"))

    # ── Notifications ────────────────────────────────────────────────────────
    notifs_raw = [
        dict(title="Bloomify App Deadline in 20 Days", message=f"Bloomify Mobile App deadline is {(today + timedelta(days=20)).strftime('%d %b %Y')}. AR try-on feature in progress.", ntype="deadline"),
        dict(title="Payment Received TechVista Rs.74000", message="Milestone 2 payment of Rs.74,000 confirmed from Rahul Mehta / TechVista Solutions.", ntype="payment"),
        dict(title="Invoice Sent INV-SHR-FORMAL-002", message="Invoice of Rs.79,960 sent to Priya Kapoor (Bloomify). Due in 25 days.", ntype="invoice"),
        dict(title="FinEdge JWT Auth Task Due in 3 Days", message=f"Task JWT auth 2FA setup for FinEdge due on {(today + timedelta(days=3)).strftime('%d %b %Y')}.", ntype="task"),
        dict(title="LogiSync Project On Hold", message="Fleet Management System on hold. Divya Menon to confirm reactivation end of month.", ntype="project"),
        dict(title="StyloAI Proposal Follow-up Reminder", message="Follow up with Tanvi Kulkarni StyloAI about the proposal sent last week.", ntype="project"),
    ]

    notifc = 0
    for ntf in notifs_raw:
        if not Notification.objects.filter(user=user, title=ntf["title"]).exists():
            Notification.objects.create(user=user, title=ntf["title"],
                                        message=ntf["message"], notification_type=ntf["ntype"])
            notifc += 1
    cmd.stdout.write(cmd.style.SUCCESS(f"{notifc} notifications created"))

    # ── Calendar Events ──────────────────────────────────────────────────────
    events_raw = [
        dict(title="Client Demo Call TechVista ERP", etype="meeting", start=timezone.now() + timedelta(days=2, hours=2), proj=projects["TechVista Enterprise ERP Portal"], desc="Sprint 6 demo with Rahul Mehta team."),
        dict(title="Bloomify AR Feature Deadline", etype="deadline", start=timezone.now() + timedelta(days=5), proj=projects["Bloomify Mobile App iOS and Android"], desc="AR try-on must be completed and tested."),
        dict(title="Payment Due FinEdge Dashboard", etype="payment", start=timezone.now() + timedelta(days=25), proj=projects["FinEdge Trading Dashboard"], desc="Final 50% Rs.47,500 due from Arjun Nair."),
        dict(title="Discovery Call StyloAI Tanvi", etype="meeting", start=timezone.now() + timedelta(days=7, hours=4), proj=None, desc="Initial requirements for AI fashion app."),
        dict(title="CA Meeting GST Q2 Filing Prep", etype="reminder", start=timezone.now() + timedelta(days=10, hours=3), proj=None, desc="Quarterly GST filing preparation with CA."),
        dict(title="HealthNest Video Module Review", etype="meeting", start=timezone.now() + timedelta(days=14, hours=2), proj=projects["HealthNest Patient Portal"], desc="WebRTC review with Sneha Joshi team."),
        dict(title="RealEstateHub Final Delivery", etype="deadline", start=timezone.now() + timedelta(days=15), proj=projects["RealEstateHub Property Listing Portal"], desc="Property portal handover to Vikram Patil."),
    ]

    evc = 0
    for ev in events_raw:
        if not CalendarEvent.objects.filter(user=user, title=ev["title"]).exists():
            CalendarEvent.objects.create(user=user, title=ev["title"], event_type=ev["etype"],
                                         start_time=ev["start"], project=ev.get("proj"),
                                         description=ev.get("desc", ""))
            evc += 1
    cmd.stdout.write(cmd.style.SUCCESS(f"{evc} calendar events created"))

    # ── Activity Logs ────────────────────────────────────────────────────────
    logs = [
        ("login", "user", uuid.uuid4(), "Shrinika logged into FreelanceTrack Dashboard"),
        ("create", "client", clients["Mohammed Al-Rashid"].id, "Added Dubai Tech Group LLC"),
        ("create", "project", projects["Dubai Tech Group Smart City Dashboard"].id, "Created Smart City Dashboard"),
        ("status_change", "project", projects["Dubai Tech Group Smart City Dashboard"].id, "Smart City Dashboard marked Completed"),
        ("payment_received", "payment", uuid.uuid4(), "Final payment Rs.3,20,000 from Dubai Tech Group"),
        ("create", "project", projects["Nexus App SaaS Analytics Platform"].id, "New project Nexus SaaS Analytics created"),
        ("update", "project", projects["TechVista Enterprise ERP Portal"].id, "ERP progress updated to 68%"),
        ("create", "task", uuid.uuid4(), "JWT auth 2FA task added to FinEdge Dashboard"),
        ("create", "invoice", uuid.uuid4(), "Invoice INV-SHR-FORMAL-003 sent to James Carter"),
        ("profile_updated", "user", uuid.uuid4(), "Profile skills and portfolio updated"),
    ]
    for action, m_type, m_id, desc in logs:
        ActivityLog.objects.create(user=user, action=action, model_type=m_type,
                                   model_id=m_id, description=desc)

    cmd.stdout.write("")
    cmd.stdout.write(cmd.style.MIGRATE_HEADING("=" * 55))
    cmd.stdout.write(cmd.style.SUCCESS("Shrinika Demo Account Ready!"))
    cmd.stdout.write(cmd.style.MIGRATE_HEADING("=" * 55))
    cmd.stdout.write("  Username  : Shrinika")
    cmd.stdout.write("  Password  : Team@123456")
    cmd.stdout.write("  Email     : shrinika@freelancetrack.demo")
    cmd.stdout.write(f"  Clients   : {len(clients)} (10 active, 1 inactive, 1 prospective)")
    cmd.stdout.write(f"  Projects  : {len(projects)}")
    cmd.stdout.write(f"  Tasks     : {tc}")
    cmd.stdout.write(f"  Payments  : {pc}")
    cmd.stdout.write(f"  Incomes   : {ic}")
    cmd.stdout.write(f"  Expenses  : {ec}")
    cmd.stdout.write(f"  Invoices  : {invc}")
    cmd.stdout.write(f"  Notes     : {nc}")
    cmd.stdout.write(f"  Notifs    : {notifc}")
    cmd.stdout.write(f"  Events    : {evc}")
    cmd.stdout.write(cmd.style.MIGRATE_HEADING("=" * 55))
'''

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(CMD)

print(f"Written: {TARGET}")
print(f"Size: {len(CMD)} chars")
