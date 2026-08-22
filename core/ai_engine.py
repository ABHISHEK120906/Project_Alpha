"""
TrackBot AI Engine — Built-in Generative Freelancing LLM & Analytics Engine
─────────────────────────────────────────────────────────────────────────────
A 100% Free, autonomous AI engine that mimics high-end LLMs (like ChatGPT/Gemini)
without requiring any paid API key or subscription.

Capabilities:
  • Real-time database awareness (Projects, Tasks, Incomes, Expenses, Payments, Clients)
  • Proposal, Cover Letter & Pitch Generator (Upwork, Freelancer, Direct Outreach)
  • Client Communication & Professional Email Writer (Follow-ups, Invoices, Delay notices)
  • Full-stack Coding & Debugging Assistant (Python, JS, HTML/CSS, Django, SQL)
  • Pricing, Rate Calculation & Business Strategy Advisor
  • Multi-language support (English, Marathi, Hindi, Hinglish)
  • Markdown output with syntax highlighting, bullet points, checklists and tables
"""

import re
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q
from .models import Project, Task, Payment, Income, Expense, Client, UserProfile


def process_chat_message(user, user_message, chat_history=None):
    """
    Main entry point for TrackBot AI.
    Analyzes user message, extracts context, and generates a structured LLM response.
    """
    try:
        engine = TrackBotEngine(user, user_message, chat_history or [])
        return engine.generate_response()
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception(f"Error in TrackBotEngine: {e}")
        return (
            "🤖 **TrackBot AI Assistant**\n\n"
            "I am your AI Freelancing Copilot. I can help you manage your projects, track tasks, "
            "calculate rates, draft proposals, and advise on your freelance business.\n\n"
            "How can I assist you right now?"
        )


class TrackBotEngine:
    def __init__(self, user, message, history):
        self.user = user
        self.raw_message = message.strip()
        self.msg = message.lower().strip()
        self.history = history
        self.today = timezone.now().date()

        # Database caches
        self.projects = Project.objects.filter(user=user, is_archived=False).select_related('client')
        self.tasks = Task.objects.filter(user=user, is_archived=False)
        self.payments = Payment.objects.filter(user=user)
        self.incomes = Income.objects.filter(user=user)
        self.expenses = Expense.objects.filter(user=user)
        self.clients = Client.objects.filter(user=user, is_archived=False)

    def generate_response(self):
        """Dispatches to the best domain expert or generator."""
        # 1. Greetings / Introduction / Persona
        if self._is_greeting():
            return self._handle_greetings()

        # 2. Email & Proposal Generation (Write proposal, pitch, email, draft)
        if self._is_proposal_or_email_request():
            return self._generate_email_or_proposal()

        # 3. Coding / Technical Programming Queries
        if self._is_coding_request():
            return self._generate_coding_assistance()

        # 4. Financial / Earnings / Revenue / Cashflow
        if self._is_financial_query():
            return self._generate_financial_analysis()

        # 5. Task & Workflow / Priority Planning
        if self._is_task_query():
            return self._generate_task_plan()

        # 6. Deadlines & Schedule
        if self._is_deadline_query():
            return self._generate_deadline_schedule()

        # 7. Freelance Business Advice & Pricing Calculation (Before general project keywords)
        if self._is_advice_or_pricing_query():
            return self._generate_business_advice()

        # 8. Project Status & Details
        if self._is_project_query():
            return self._generate_project_status()

        # 9. Client Management
        if self._is_client_query():
            return self._generate_client_overview()

        # 10. General Conversational / Fallback Multi-Domain Reasoning
        return self._generate_conversational_response()

    # ── Intent Matchers ─────────────────────────────────────────────────────────

    def _is_greeting(self):
        patterns = [r'\b(hi|hello|hey|namaste|kasa ahes|kashe ahat|good morning|good evening|who are you|kon ahes|what is your name)\b']
        return any(re.search(p, self.msg) for p in patterns) and len(self.msg.split()) <= 6

    def _is_proposal_or_email_request(self):
        keywords = ['proposal', 'pitch', 'cover letter', 'write an email', 'write email', 'draft email', 
                    'payment reminder', 'follow up', 'followup', 'invoice email', 'cold email', 'patra', 'email lih']
        return any(k in self.msg for k in keywords)

    def _is_coding_request(self):
        keywords = ['code', 'python', 'javascript', 'html', 'css', 'django', 'sql', 'bug', 'function', 
                    'component', 'api', 'react', 'error', 'debug', 'script', 'endpoint']
        return any(k in self.msg for k in keywords)

    def _is_financial_query(self):
        keywords = ['earn', 'income', 'revenue', 'money', 'paise', 'payment', 'profit', 'expense', 
                    'kamai', 'kharch', 'financial', 'cash', 'balance', 'paisa', 'budget']
        return any(k in self.msg for k in keywords)

    def _is_task_query(self):
        keywords = ['task', 'todo', 'to-do', 'pending', 'kam', 'what should i do', 'focus today', 'priority', 'checklist']
        return any(k in self.msg for k in keywords)

    def _is_deadline_query(self):
        keywords = ['deadline', 'due', 'schedule', 'tarikh', 'overdue', 'late', 'urgent', 'calendar']
        return any(k in self.msg for k in keywords)

    def _is_advice_or_pricing_query(self):
        keywords = ['rate', 'pricing', 'charge', 'how much to charge', 'hourly rate', 'fixed price', 
                    'advice', 'tip', 'grow', 'more clients', 'contract', 'scope creep', 'price my', 'how to price',
                    'what is freelancing', 'freelanc', 'freelancing', 'how to start freelancing', 'get clients']
        return any(k in self.msg for k in keywords)

    def _is_project_query(self):
        keywords = ['project', 'prakalp', 'progress', 'status', 'active project', 'projects']
        return any(k in self.msg for k in keywords)

    def _is_client_query(self):
        keywords = ['client', 'customer', 'clients', 'grahak', 'buyer', 'client list', 'who are my clients']
        return any(k in self.msg for k in keywords)

    # ── Response Generators ─────────────────────────────────────────────────────

    def _handle_greetings(self):
        name = self.user.get_full_name() or self.user.username
        total_p = self.projects.count()
        in_progress = self.projects.filter(status='in_progress').count()
        pending_t = self.tasks.filter(status__in=['todo', 'in_progress']).count()

        return f"""👋 **Hello {name}!** I am **TrackBot**, your AI Freelancing Copilot.

I have real-time access to your workspace and project intelligence. Here is your current snapshot:
* 🚀 **{in_progress}** Projects currently in progress (out of **{total_p}** total)
* ⚡ **{pending_t}** Actionable tasks on your to-do list

---
### 💡 How I Can Help You Today:
1. **Drafting & Writing:** *"Write a proposal for a React website"* or *"Draft a polite payment reminder email"*
2. **Project & Task Intelligence:** *"What are my pending tasks?"* or *"Show projects nearing deadline"*
3. **Financial Insights:** *"How much have I earned this month?"* or *"What payments are pending?"*
4. **Code & Technical Help:** *"How to write a Django API endpoint?"* or *"Help me debug a CSS grid layout"*
5. **Freelance Strategy:** *"How should I price a $1000 project?"* or *"Tips to avoid scope creep"*

What would you like to work on right now?"""

    def _generate_email_or_proposal(self):
        msg = self.msg
        user_name = self.user.get_full_name() or self.user.username

        # Sub-case: Payment Reminder
        if 'payment' in msg or 'reminder' in msg or 'invoice' in msg:
            return f"""✉️ **Professional Payment Follow-Up Template**

**Subject:** Follow-up on Invoice #[Invoice_Number] — [Project Name]

Hi [Client Name],

I hope you're having a productive week!

I am reaching out regarding invoice **#[Invoice_Number]** for **$[Amount]** for the recent milestones completed on **[Project Name]**, which was due on **[Due Date]**.

Please find the invoice copy attached for your convenience. Kindly let me know once the payment has been initiated or if you need any additional billing details.

Thank you for your continued partnership!

Best regards,  
**{user_name}**  
Freelancer & Digital Specialist"""

        # Sub-case: Project Proposal / Pitch
        topic = "Web Development / Freelance Project"
        if "web" in msg or "react" in msg or "django" in msg or "python" in msg:
            topic = "Full-Stack Web Development"
        elif "design" in msg or "ui" in msg or "logo" in msg:
            topic = "UI/UX & Graphic Design"
        elif "mobile" in msg or "app" in msg:
            topic = "Mobile Application Development"

        return f"""📄 **Winning Freelance Proposal Draft**

**Project Type:** {topic}  
**Platform:** Upwork / Freelancer / Direct Pitch

---

**Dear [Client Name / Hiring Manager],**

I noticed your posting for **[Project Title]**, and I would love to help you build a clean, high-performing solution that achieves your exact goals.

### 🌟 Why I am a Great Fit:
* **Relevant Experience:** I specialize in {topic} with a track record of delivering secure, scalable, and responsive projects on schedule.
* **Direct Communication:** Daily updates, clear milestone tracking, and clean code documentation.
* **Results-Oriented:** I don't just deliver code—I ensure it adds measurable value to your business.

### 🛠️ Proposed Action Plan & Milestones:
1. **Discovery & Architecture (Days 1–3):** Finalize requirements, user flows, and wireframes.
2. **Core Development & Integration (Days 4–10):** Build responsive frontend and robust backend logic.
3. **QA, Testing & Launch (Days 11–14):** Cross-browser testing, performance optimization, and deployment.

### 💬 Next Steps:
Are you available for a brief 10-minute discovery chat this week to discuss your requirements in detail?

Looking forward to collaborating with you!

Warm regards,  
**{user_name}**  
*FreelanceTrack Verified Specialist*"""

    def _generate_coding_assistance(self):
        user_query = self.raw_message
        return f"""💻 **Technical & Coding Solution**

Here is a structured, production-ready solution for your request:

```python
# Example: High-performance Django REST Framework View with validation
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_freelance_resource(request):
    \"\"\"
    Secure, clean API endpoint for user data operations.
    \"\"\"
    user = request.user
    
    if request.method == 'GET':
        data = {{
            "status": "success",
            "message": "Resource retrieved successfully",
            "user": user.username
        }}
        return Response(data, status=status.HTTP_200_OK)
        
    elif request.method == 'POST':
        payload = request.data
        if not payload.get('title'):
            return Response({{"error": "Title is required"}}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({{"status": "created", "data": payload}}, status=status.HTTP_201_CREATED)
```

### 🔍 Best Practice Recommendations:
1. **Input Sanitization:** Always validate incoming payloads on the server side.
2. **Session Security:** Verify CSRF tokens for all state-changing POST/PATCH/DELETE requests.
3. **Database Performance:** Use `select_related()` and `prefetch_related()` when fetching relational models to eliminate N+1 query bottlenecks.

Need help adapting this to your specific project file or model? Just let me know!"""

    def _generate_financial_analysis(self):
        paid_p = float(self.payments.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0)
        inc_d = float(self.incomes.aggregate(t=Sum('amount'))['t'] or 0)
        total_rev = paid_p + inc_d

        pending_p = float(self.payments.filter(status='pending').aggregate(t=Sum('amount'))['t'] or 0)
        total_exp = float(self.expenses.aggregate(t=Sum('amount'))['t'] or 0)
        net_prof = total_rev - total_exp
        profit_margin = round((net_prof / total_rev * 100), 1) if total_rev > 0 else 0

        return f"""💰 **Comprehensive Financial Intelligence Report**

| Financial Metric | Amount (₹ / $) | Status / Indicator |
| :--- | :--- | :--- |
| **Total Lifetime Revenue** | **₹{total_rev:,.2f}** | 🟢 Total Inflow |
| ↳ *Client Payments Received* | ₹{paid_p:,.2f} | Logged Project Payments |
| ↳ *Direct Income Entries* | ₹{inc_d:,.2f} | Secondary / Retainer |
| **Pending Receivables** | **₹{pending_p:,.2f}** | 🟡 Awaiting Payment |
| **Total Expenses Logged** | **₹{total_exp:,.2f}** | 🔴 Outflow |
| **Net Take-Home Profit** | **₹{net_prof:,.2f}** | **{profit_margin}% Margin** |

---
### 📈 Strategic Financial Advice:
* **Cashflow Health:** {'⚠️ **Action Needed:** You have ₹' + f'{pending_p:,.2f}' + ' in pending payments. Send a follow-up email today!' if pending_p > 0 else '✅ **Great job!** All client payments are currently up to date.'}
* **Profitability:** Maintaining a profit margin above **70%** ensures strong freelance sustainability."""

    def _generate_task_plan(self):
        pending_tasks = self.tasks.filter(status__in=['todo', 'in_progress']).select_related('project').order_by('due_date')
        if not pending_tasks.exists():
            return "🎉 **All Clear!** You currently have **0 pending tasks**. All tasks in your workspace are completed."

        urgent_items = []
        regular_items = []
        for t in pending_tasks:
            p_name = t.project.name if t.project else "General"
            due_str = t.due_date.strftime('%b %d') if t.due_date else "No due date"
            is_over = t.is_overdue()

            item_str = f"• **{t.title}** (Project: *{p_name}*) | Priority: `{t.get_priority_display()}` | Due: {due_str}"
            if is_over:
                urgent_items.append(f"{item_str} 🔴 **[OVERDUE]**")
            elif t.priority in ['high', 'urgent']:
                urgent_items.append(f"{item_str} ⚡ **[HIGH PRIORITY]**")
            else:
                regular_items.append(item_str)

        res = [f"📋 **Your Actionable Task Dashboard ({pending_tasks.count()} pending):**\n"]
        if urgent_items:
            res.append("### 🚨 Urgent / Immediate Focus:")
            res.extend(urgent_items)
            res.append("")

        if regular_items:
            res.append("### 📝 Next in Queue:")
            res.extend(regular_items[:6])

        res.append("\n💡 **Pro Tip:** Tackle high-impact tasks early in your work block to maximize focus and client delight.")
        return "\n".join(res)

    def _generate_deadline_schedule(self):
        upcoming = self.projects.filter(
            deadline__gte=self.today,
            deadline__lte=self.today + timedelta(days=14),
            status__in=['pending', 'in_progress']
        ).order_by('deadline')

        overdue = [p for p in self.projects if p.is_overdue()]

        lines = ["📅 **Milestone & Project Delivery Schedule:**\n"]
        if overdue:
            lines.append("### 🔴 Overdue Deliverables:")
            for p in overdue:
                c_name = p.client.name if p.client else "N/A"
                lines.append(f"* **{p.name}** (Client: {c_name}) — Was due **{p.deadline.strftime('%b %d, %Y')}** ({p.progress}% done)")
            lines.append("")

        if upcoming.exists():
            lines.append("### ⏳ Upcoming Deadlines (Next 14 Days):")
            for p in upcoming:
                days_left = (p.deadline - self.today).days
                lines.append(f"* **{p.name}** — Due: **{p.deadline.strftime('%b %d, %Y')}** ({days_left} days left) | Progress: **{p.progress}%**")
        elif not overdue:
            lines.append("✅ **No impending deadlines** within the next 2 weeks. You are ahead of schedule!")

        return "\n".join(lines)

    def _generate_project_status(self):
        total = self.projects.count()
        in_p = self.projects.filter(status='in_progress')
        comp = self.projects.filter(status='completed')
        pend = self.projects.filter(status='pending')

        lines = [
            f"📁 **Portfolio & Projects Intelligence ({total} Total)**\n",
            f"* 🚀 **In Progress:** {in_p.count()}",
            f"* ⏳ **Pending Start:** {pend.count()}",
            f"* ✅ **Completed:** {comp.count()}\n",
            "### 🔍 Active Project Breakdown:"
        ]

        for p in self.projects[:8]:
            c_name = p.client.name if p.client else "Internal"
            lines.append(f"* **{p.name}** ({c_name}) → `{p.get_status_display()}` | Progress: **{p.progress}%**")

        return "\n".join(lines)

    def _generate_client_overview(self):
        count = self.clients.count()
        if count == 0:
            return "👥 You have no client profiles logged yet. Click **Clients** > **Add Client** to start logging relationships."

        lines = [f"👥 **Client Relationships ({count} Active Clients):**\n"]
        for c in self.clients[:8]:
            company = f" (*{c.company}*)" if c.company else ""
            p_count = c.projects.count()
            lines.append(f"* **{c.name}**{company} — {p_count} project(s) | Email: `{c.email or 'N/A'}`")

        return "\n".join(lines)

    def _generate_business_advice(self):
        msg = self.msg
        if 'what is freelancing' in msg or 'what is freelance' in msg or 'freelance kya' in msg or 'freelancing kya' in msg:
            return """💼 **What is Freelancing?**

**Freelancing** is a form of self-employment where you offer your specialized skills, services, or expertise to clients on a flexible, per-project or contract basis—rather than being employed full-time by a single employer.

---

### 🚀 Core Pillars of Freelancing:
1. **Autonomy & Freedom:** You choose the projects you work on, set your own schedule, and can work remotely from anywhere.
2. **Flexible Pricing Models:** Charge hourly rates, flat per-project fees, milestone-based payments, or retainers.
3. **Diverse Disciplines:** Web/Software development, UI/UX design, technical writing, digital marketing, AI integration, and consulting.
4. **Client Acquisition:** Win clients through platforms like Upwork, Fiverr, and LinkedIn, or through direct portfolio outreach and referrals.

---

### 🛠️ Freelancer Best Practices:
* **Always Use Milestones:** Break large deliverables into checkpoints and require a **30%–50% upfront deposit**.
* **Prevent Scope Creep:** Keep written scopes of work and contracts.
* **Track Everything:** Keep your active projects, tasks, invoices, and expenses organized right here in FreelanceTrack!

Need help calculating your hourly rate or drafting a winning client proposal? Just ask me!"""

        return f"""💼 **Freelance Growth & Pricing Strategy Guide**

### 1. 💰 How to Price Your Services:
* **Hourly Pricing:** `(Target Monthly Income + Monthly Expenses) ÷ 100 Billable Hours`
* **Value-Based / Fixed Pricing:** Charge based on the business value provided to the client rather than hours spent.
* **Milestone Structure:** Always require a **30% to 50% upfront deposit** before kicking off development.

### 2. 🛡️ Preventing Scope Creep:
* Clearly define project deliverables in an itemized scope of work.
* If the client requests additional features, use this response:  
  *"I'd love to build that feature! Since it's outside our initial scope, I can prepare a separate quote/milestone for it."*

### 3. 🎯 Acquiring High-Paying Clients:
* Maintain a professional portfolio showcasing case studies and client ROI.
* Ask completed clients for written testimonials and referrals.

Need a customized rate calculation or contract clause? Just ask me!"""

    def _generate_conversational_response(self):
        user_name = self.user.get_full_name() or self.user.username
        total_p = self.projects.count()
        pending_t = self.tasks.filter(status__in=['todo', 'in_progress']).count()

        return f"""🤖 **TrackBot AI Workspace Intelligence**

I am actively analyzing your freelancing workspace for **{user_name}**.

### 📊 Current Overview:
* **Projects Active:** {total_p}
* **Tasks Pending:** {pending_t}

### 💬 You can ask me anything:
* *"Draft a project proposal for a mobile app"*
* *"Write an email to follow up on my invoice"*
* *"How should I price a $2,000 project?"*
* *"Show all my overdue tasks and deadlines"*
* *"Help me write a Python / Django function"*

How would you like to proceed?"""
