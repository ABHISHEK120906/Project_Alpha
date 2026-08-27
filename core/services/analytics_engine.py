"""
Freelancer Intelligence Platform — Data Analytics & Business Intelligence Engine
=================================================================================
Provides rigorous data profiling, quality audit, descriptive statistics,
exploratory data analysis (EDA), correlation matrix calculations, outlier detection,
trend trajectory analysis, and algorithmic business insight generation based on
real database models and user data.
"""

import math
from datetime import datetime, date, timedelta
from collections import Counter, defaultdict
from decimal import Decimal

from django.db.models import Sum, Avg, Count, Min, Max, Q, F
from django.utils import timezone

from core.models import Client, Project, Payment, Task, Income, Expense, Invoice


# ==============================================================================
# 1. HELPER MATHEMATICAL & STATISTICAL UTILITIES
# ==============================================================================

def to_float(val, default=0.0):
    """Safely cast numeric/Decimal value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def compute_median(sorted_nums):
    """Calculate the exact median from a sorted list of numbers."""
    n = len(sorted_nums)
    if n == 0:
        return None
    mid = n // 2
    if n % 2 == 1:
        return sorted_nums[mid]
    return (sorted_nums[mid - 1] + sorted_nums[mid]) / 2.0


def compute_percentile(sorted_nums, p):
    """Calculate the p-th percentile (0-100) from a sorted list of numbers."""
    n = len(sorted_nums)
    if n == 0:
        return None
    if n == 1:
        return sorted_nums[0]
    
    k = (n - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_nums[int(k)]
    d0 = sorted_nums[int(f)] * (c - k)
    d1 = sorted_nums[int(c)] * (k - f)
    return d0 + d1


def compute_descriptive_stats(numbers):
    """
    Computes a comprehensive statistical profile for a numeric array:
    count, min, max, range, mean, median, mode, variance, std_dev,
    Q1 (25th), Q2 (50th), Q3 (75th), IQR, and skewness indication.
    """
    clean = [to_float(x) for x in numbers if x is not None and not (isinstance(x, float) and math.isnan(x))]
    n = len(clean)
    
    if n == 0:
        return {
            'count': 0, 'min': None, 'max': None, 'range': None,
            'mean': None, 'median': None, 'mode': None,
            'variance': None, 'std_dev': None,
            'q1': None, 'q2': None, 'q3': None, 'iqr': None,
            'skewness': 'N/A', 'is_sufficient': False
        }
    
    sorted_nums = sorted(clean)
    val_min = sorted_nums[0]
    val_max = sorted_nums[-1]
    val_range = val_max - val_min
    val_mean = sum(sorted_nums) / n
    val_median = compute_median(sorted_nums)
    
    # Mode calculation
    counts = Counter(sorted_nums)
    max_freq = max(counts.values()) if counts else 0
    modes = [k for k, v in counts.items() if v == max_freq]
    val_mode = modes[0] if max_freq > 1 or n == 1 else None
    
    # Variance and standard deviation (sample variance if n > 1)
    if n > 1:
        variance = sum((x - val_mean) ** 2 for x in sorted_nums) / (n - 1)
        std_dev = math.sqrt(variance)
    else:
        variance = 0.0
        std_dev = 0.0
        
    q1 = compute_percentile(sorted_nums, 25)
    q2 = val_median
    q3 = compute_percentile(sorted_nums, 75)
    p10 = compute_percentile(sorted_nums, 10)
    p90 = compute_percentile(sorted_nums, 90)
    iqr = (q3 - q1) if (q3 is not None and q1 is not None) else 0.0
    lower_whisker = max(val_min, q1 - 1.5 * iqr) if q1 is not None else val_min
    upper_whisker = min(val_max, q3 + 1.5 * iqr) if q3 is not None else val_max
    
    # Skewness classification based on mean vs median
    if std_dev > 0.0001:
        skew_diff = (val_mean - val_median) / std_dev
        if abs(skew_diff) < 0.2:
            skew_label = 'Approximately Symmetric'
        elif skew_diff > 0.2:
            skew_label = 'Positively Skewed (Right-tailed)'
        else:
            skew_label = 'Negatively Skewed (Left-tailed)'
    else:
        skew_label = 'Uniform / Zero Variance'
        
    return {
        'count': n,
        'min': round(val_min, 2),
        'max': round(val_max, 2),
        'range': round(val_range, 2),
        'mean': round(val_mean, 2),
        'median': round(val_median, 2),
        'mode': round(val_mode, 2) if val_mode is not None else 'No unique mode',
        'variance': round(variance, 2),
        'std_dev': round(std_dev, 2),
        'p10': round(p10, 2) if p10 is not None else None,
        'q1': round(q1, 2) if q1 is not None else None,
        'q2': round(q2, 2) if q2 is not None else None,
        'q3': round(q3, 2) if q3 is not None else None,
        'p90': round(p90, 2) if p90 is not None else None,
        'iqr': round(iqr, 2) if iqr is not None else None,
        'lower_whisker': round(lower_whisker, 2),
        'upper_whisker': round(upper_whisker, 2),
        'skewness': skew_label,
        'is_sufficient': n >= 2
    }


# ==============================================================================
# 2. DATASET EXTRACTION & PROFILING ENGINE
# ==============================================================================

class DataAnalyticsEngine:
    """
    Main Data Analytics engine providing real-time data inspection,
    profiling, quality metrics, EDA, statistical summaries, correlation,
    and business intelligence reporting for a specific user.
    """

    def __init__(self, user, filters=None):
        self.user = user
        self.filters = filters or {}
        self.today = timezone.now().date()
        self._load_datasets()

    def _load_datasets(self):
        """Load and filter real querysets for the current user."""
        projects_qs = Project.objects.filter(user=self.user, is_archived=False).select_related('client')
        payments_qs = Payment.objects.filter(user=self.user).select_related('project', 'project__client')
        clients_qs = Client.objects.filter(user=self.user, is_archived=False)
        tasks_qs = Task.objects.filter(user=self.user, is_archived=False).select_related('project')
        incomes_qs = Income.objects.filter(user=self.user)
        expenses_qs = Expense.objects.filter(user=self.user)

        # Apply optional filters
        client_filter = self.filters.get('client')
        if client_filter:
            projects_qs = projects_qs.filter(client_id=client_filter)
            payments_qs = payments_qs.filter(project__client_id=client_filter)

        status_filter = self.filters.get('status')
        if status_filter:
            projects_qs = projects_qs.filter(status=status_filter)

        date_from = self.filters.get('date_from')
        date_to = self.filters.get('date_to')
        if date_from:
            try:
                d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                payments_qs = payments_qs.filter(Q(paid_date__gte=d_from) | Q(created_at__date__gte=d_from))
                projects_qs = projects_qs.filter(created_at__date__gte=d_from)
            except ValueError:
                pass
        if date_to:
            try:
                d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                payments_qs = payments_qs.filter(Q(paid_date__lte=d_to) | Q(created_at__date__lte=d_to))
                projects_qs = projects_qs.filter(created_at__date__lte=d_to)
            except ValueError:
                pass

        self.projects_qs = projects_qs
        self.payments_qs = payments_qs
        self.clients_qs = clients_qs
        self.tasks_qs = tasks_qs
        self.incomes_qs = incomes_qs
        self.expenses_qs = expenses_qs

    # --------------------------------------------------------------------------
    # Phase 3: Data Profiling
    # --------------------------------------------------------------------------
    def get_data_profiles(self):
        """
        Profiles the 4 main business tables (Projects, Payments, Clients, Tasks).
        Calculates column types, unique values, null counts, null %, and ranges.
        """
        profiles = {}

        # 1. Projects Table Profile
        projects_data = []
        for p in self.projects_qs:
            duration = (p.deadline - p.start_date).days if (p.start_date and p.deadline) else None
            projects_data.append({
                'id': str(p.id),
                'name': p.name,
                'client': p.client.name if p.client else None,
                'status': p.status,
                'priority': p.priority,
                'budget': to_float(p.budget) if p.budget is not None else None,
                'progress': p.progress,
                'start_date': p.start_date.isoformat() if p.start_date else None,
                'deadline': p.deadline.isoformat() if p.deadline else None,
                'duration_days': duration,
                'created_at': p.created_at.date().isoformat()
            })

        profiles['projects'] = self._profile_records_table(
            name="Projects Dataset",
            records=projects_data,
            schema={
                'name': {'type': 'String', 'is_numeric': False},
                'client': {'type': 'String (Categorical / FK)', 'is_numeric': False},
                'status': {'type': 'Categorical', 'is_numeric': False},
                'priority': {'type': 'Categorical', 'is_numeric': False},
                'budget': {'type': 'Float (Currency)', 'is_numeric': True},
                'progress': {'type': 'Integer (0-100 %)', 'is_numeric': True},
                'start_date': {'type': 'Date', 'is_numeric': False},
                'deadline': {'type': 'Date', 'is_numeric': False},
                'duration_days': {'type': 'Integer (Days)', 'is_numeric': True},
            }
        )

        # 2. Payments Table Profile
        payments_data = []
        for pm in self.payments_qs:
            payments_data.append({
                'id': str(pm.id),
                'project': pm.project.name if pm.project else None,
                'client': pm.project.client.name if (pm.project and pm.project.client) else None,
                'amount': to_float(pm.amount),
                'status': pm.status,
                'payment_method': pm.payment_method,
                'due_date': pm.due_date.isoformat() if pm.due_date else None,
                'paid_date': pm.paid_date.isoformat() if pm.paid_date else None,
                'created_at': pm.created_at.date().isoformat()
            })

        profiles['payments'] = self._profile_records_table(
            name="Payments Dataset",
            records=payments_data,
            schema={
                'project': {'type': 'String (FK)', 'is_numeric': False},
                'client': {'type': 'String (FK)', 'is_numeric': False},
                'amount': {'type': 'Float (Currency)', 'is_numeric': True},
                'status': {'type': 'Categorical', 'is_numeric': False},
                'payment_method': {'type': 'Categorical', 'is_numeric': False},
                'due_date': {'type': 'Date', 'is_numeric': False},
                'paid_date': {'type': 'Date', 'is_numeric': False},
            }
        )

        # 3. Clients Table Profile
        clients_data = []
        for c in self.clients_qs:
            clients_data.append({
                'id': str(c.id),
                'name': c.name,
                'email': c.email,
                'company': c.company or None,
                'status': c.status,
                'phone': c.phone or None,
                'created_at': c.created_at.date().isoformat()
            })

        profiles['clients'] = self._profile_records_table(
            name="Clients Dataset",
            records=clients_data,
            schema={
                'name': {'type': 'String', 'is_numeric': False},
                'email': {'type': 'Email / String', 'is_numeric': False},
                'company': {'type': 'String (Optional)', 'is_numeric': False},
                'status': {'type': 'Categorical', 'is_numeric': False},
                'phone': {'type': 'String (Optional)', 'is_numeric': False},
            }
        )

        return profiles

    def _profile_records_table(self, name, records, schema):
        """Builds detailed per-column summary statistics and null/uniqueness diagnostics."""
        row_count = len(records)
        col_count = len(schema)
        columns_profile = []

        for col_name, meta in schema.items():
            vals = [r.get(col_name) for r in records]
            non_null = [v for v in vals if v is not None and v != '']
            null_count = row_count - len(non_null)
            null_pct = round((null_count / row_count) * 100.0, 1) if row_count > 0 else 0.0
            unique_count = len(set(non_null))

            col_stats = {
                'name': col_name,
                'data_type': meta['type'],
                'is_numeric': meta['is_numeric'],
                'total_rows': row_count,
                'non_null_count': len(non_null),
                'null_count': null_count,
                'null_percentage': null_pct,
                'unique_values': unique_count,
            }

            if meta['is_numeric'] and non_null:
                num_stats = compute_descriptive_stats(non_null)
                col_stats.update({
                    'min': num_stats['min'],
                    'max': num_stats['max'],
                    'mean': num_stats['mean'],
                    'median': num_stats['median'],
                    'std_dev': num_stats['std_dev'],
                })
            else:
                col_stats.update({
                    'min': 'N/A', 'max': 'N/A', 'mean': 'N/A',
                    'median': 'N/A', 'std_dev': 'N/A'
                })

            columns_profile.append(col_stats)

        # Check duplicate row keys
        unique_ids = len(set(r.get('id') for r in records if 'id' in r))
        duplicate_count = max(0, row_count - unique_ids)

        return {
            'name': name,
            'row_count': row_count,
            'column_count': col_count,
            'duplicate_count': duplicate_count,
            'columns': columns_profile,
            'is_empty': row_count == 0
        }

    # --------------------------------------------------------------------------
    # Phase 4 & 5: Data Quality Audit & Scoring Engine
    # --------------------------------------------------------------------------
    def evaluate_data_quality(self):
        """
        Calculates an empirical Data Quality Score (0-100) based on real data rules:
        - Missing values in required fields (budget, deadline, client email)
        - Inconsistent states (e.g. 100% progress but status is pending, overdue items)
        - Duplications and unlinked orphaned records
        """
        issues = []
        total_checks = 0
        passed_checks = 0

        # Check 1: Projects without defined budgets
        total_projects = self.projects_qs.count()
        if total_projects > 0:
            total_checks += 1
            missing_budget = self.projects_qs.filter(budget__isnull=True).count()
            if missing_budget > 0:
                pct = round((missing_budget / total_projects) * 100.0, 1)
                issues.append({
                    'id': 'missing_project_budget',
                    'dataset': 'Projects',
                    'issue': f'{missing_budget} project(s) have no budget specified ({pct}%)',
                    'severity': 'Medium',
                    'severity_badge': 'warning',
                    'affected_count': missing_budget,
                    'recommendation': 'Assign estimated budgets to improve revenue forecasting accuracy.'
                })
            else:
                passed_checks += 1

            # Check 2: Missing deadlines
            total_checks += 1
            missing_deadline = self.projects_qs.filter(deadline__isnull=True).count()
            if missing_deadline > 0:
                issues.append({
                    'id': 'missing_project_deadline',
                    'dataset': 'Projects',
                    'issue': f'{missing_deadline} project(s) do not have a target completion deadline',
                    'severity': 'Medium',
                    'severity_badge': 'warning',
                    'affected_count': missing_deadline,
                    'recommendation': 'Set deadlines to enable schedule tracking and overdue analysis.'
                })
            else:
                passed_checks += 1

            # Check 3: State inconsistency (progress=100% but status != completed)
            total_checks += 1
            inconsistent_status = self.projects_qs.filter(progress=100).exclude(status='completed').count()
            if inconsistent_status > 0:
                issues.append({
                    'id': 'inconsistent_project_status',
                    'dataset': 'Projects',
                    'issue': f'{inconsistent_status} project(s) show 100% progress but are not marked "Completed"',
                    'severity': 'High',
                    'severity_badge': 'danger',
                    'affected_count': inconsistent_status,
                    'recommendation': 'Synchronize project status to "Completed" to maintain clean portfolio metrics.'
                })
            else:
                passed_checks += 1

        # Check 4: Overdue Pending Payments
        total_payments = self.payments_qs.count()
        if total_payments > 0:
            total_checks += 1
            overdue_payments = self.payments_qs.filter(
                status='pending',
                due_date__lt=self.today
            ).count()
            if overdue_payments > 0:
                issues.append({
                    'id': 'overdue_pending_payments',
                    'dataset': 'Payments',
                    'issue': f'{overdue_payments} pending payment(s) are past their due date',
                    'severity': 'High',
                    'severity_badge': 'danger',
                    'affected_count': overdue_payments,
                    'recommendation': 'Send invoice reminders or follow up with clients to resolve cashflow delay.'
                })
            else:
                passed_checks += 1

            # Check 5: Paid payments missing paid_date
            total_checks += 1
            missing_paid_date = self.payments_qs.filter(status='paid', paid_date__isnull=True).count()
            if missing_paid_date > 0:
                issues.append({
                    'id': 'missing_paid_date',
                    'dataset': 'Payments',
                    'issue': f'{missing_paid_date} payment(s) marked "Paid" have no recorded receipt date',
                    'severity': 'Low',
                    'severity_badge': 'info',
                    'affected_count': missing_paid_date,
                    'recommendation': 'Log payment receipt dates for accurate month-by-month financial reconciliation.'
                })
            else:
                passed_checks += 1

        # Check 6: Clients with empty company names
        total_clients = self.clients_qs.count()
        if total_clients > 0:
            total_checks += 1
            no_company = self.clients_qs.filter(Q(company__isnull=True) | Q(company__exact='')).count()
            if no_company > 0:
                issues.append({
                    'id': 'client_missing_company',
                    'dataset': 'Clients',
                    'issue': f'{no_company} client(s) lack an associated company or organization name',
                    'severity': 'Low',
                    'severity_badge': 'info',
                    'affected_count': no_company,
                    'recommendation': 'Add company names or classify as "Individual Freelance Client".'
                })
            else:
                passed_checks += 1

        # Calculate Quality Score
        if total_checks == 0:
            score = 100
            rating = 'Optimal'
            color = '#3daa60'
        else:
            base_score = (passed_checks / total_checks) * 100.0
            # Deduct points weighted by severity
            deduction = 0
            for iss in issues:
                if iss['severity'] == 'High':
                    deduction += 15
                elif iss['severity'] == 'Medium':
                    deduction += 8
                else:
                    deduction += 3
            score = max(10, min(100, int(100 - deduction)))
            if score >= 85:
                rating = 'Excellent'
                color = '#3daa60'
            elif score >= 70:
                rating = 'Good'
                color = '#2563eb'
            elif score >= 50:
                rating = 'Moderate'
                color = '#c8881e'
            else:
                rating = 'Requires Attention'
                color = '#ae2c11'

        return {
            'quality_score': score,
            'rating': rating,
            'color': color,
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'issues': issues,
            'issues_count': len(issues)
        }

    # --------------------------------------------------------------------------
    # Phase 6 & 7: Exploratory Data Analysis & Statistical Modeling
    # --------------------------------------------------------------------------
    def get_exploratory_analysis(self):
        """
        Builds Univariate, Bivariate, and Categorical distributions on real data.
        """
        # --- Univariate 1: Project Budget Distribution ---
        budgets = [to_float(p.budget) for p in self.projects_qs if p.budget is not None]
        budget_stats = compute_descriptive_stats(budgets)

        # Budget histogram bins
        budget_histogram = self._compute_histogram_bins(budgets, num_bins=5)

        # --- Univariate 2: Payment Amount Distribution ---
        payment_amounts = [to_float(pm.amount) for pm in self.payments_qs]
        payment_stats = compute_descriptive_stats(payment_amounts)
        payment_histogram = self._compute_histogram_bins(payment_amounts, num_bins=5)

        # --- Categorical: Project Status Distribution ---
        status_counts = Counter(self.projects_qs.values_list('status', flat=True))
        total_p = sum(status_counts.values()) or 1
        status_dist = [
            {
                'status': k,
                'label': dict(Project.STATUS_CHOICES).get(k, k.capitalize()),
                'count': v,
                'percentage': round((v / total_p) * 100.0, 1)
            }
            for k, v in status_counts.items()
        ]

        # --- Categorical: Project Priority Distribution ---
        priority_counts = Counter(self.projects_qs.values_list('priority', flat=True))
        priority_dist = [
            {
                'priority': k,
                'label': dict(Project.PRIORITY_CHOICES).get(k, k.capitalize()),
                'count': v,
                'percentage': round((v / total_p) * 100.0, 1)
            }
            for k, v in priority_counts.items()
        ]

        # --- Bivariate 1: Client vs Total Revenue ---
        client_rev_map = defaultdict(lambda: {'revenue': 0.0, 'projects': 0})
        for pm in self.payments_qs.filter(status='paid'):
            c_name = pm.project.client.name if (pm.project and pm.project.client) else 'Independent'
            client_rev_map[c_name]['revenue'] += to_float(pm.amount)

        for p in self.projects_qs:
            c_name = p.client.name if p.client else 'Independent'
            client_rev_map[c_name]['projects'] += 1

        client_bivariate = [
            {'client': k, 'revenue': round(v['revenue'], 2), 'projects': v['projects']}
            for k, v in sorted(client_rev_map.items(), key=lambda x: x[1]['revenue'], reverse=True)[:8]
        ]

        # --- Bivariate 2: Project Budget vs Actual Paid Realization ---
        scatter_budget_vs_paid = []
        for p in self.projects_qs:
            paid_sum = self.payments_qs.filter(project=p, status='paid').aggregate(t=Sum('amount'))['t'] or 0
            scatter_budget_vs_paid.append({
                'name': p.name,
                'client': p.client.name if p.client else 'N/A',
                'budget': to_float(p.budget),
                'paid': to_float(paid_sum),
                'progress': p.progress,
                'status': p.status
            })

        # --- Bivariate 3: Project Duration vs Contract Value ---
        duration_bivariate = []
        for p in self.projects_qs:
            if p.start_date and p.deadline:
                dur_days = max(1, (p.deadline - p.start_date).days)
                duration_bivariate.append({
                    'name': p.name,
                    'duration_days': dur_days,
                    'budget': to_float(p.budget),
                    'status': p.status
                })

        return {
            'budget_stats': budget_stats,
            'budget_histogram': budget_histogram,
            'payment_stats': payment_stats,
            'payment_histogram': payment_histogram,
            'status_distribution': status_dist,
            'priority_distribution': priority_dist,
            'client_bivariate': client_bivariate,
            'scatter_budget_vs_paid': scatter_budget_vs_paid,
            'duration_bivariate': duration_bivariate,
        }

    def _compute_histogram_bins(self, values, num_bins=5):
        """Generates dynamic histogram bins for continuous numeric distributions."""
        if not values or len(values) < 2:
            return {'bins': [], 'counts': [], 'is_empty': True}

        v_min = min(values)
        v_max = max(values)
        if v_min == v_max:
            return {
                'bins': [f"${round(v_min, 1)}"],
                'counts': [len(values)],
                'is_empty': False
            }

        bin_width = (v_max - v_min) / num_bins
        bins_labels = []
        counts = [0] * num_bins

        for i in range(num_bins):
            b_start = v_min + (i * bin_width)
            b_end = v_min + ((i + 1) * bin_width)
            bins_labels.append(f"${round(b_start, 0):,.0f} - ${round(b_end, 0):,.0f}")

        for val in values:
            idx = int((val - v_min) / bin_width)
            if idx >= num_bins:
                idx = num_bins - 1
            counts[idx] += 1

        return {
            'bins': bins_labels,
            'counts': counts,
            'is_empty': False
        }

    # --------------------------------------------------------------------------
    # Phase 11: Correlation Matrix & Bivariate Relationships
    # --------------------------------------------------------------------------
    def calculate_correlation_matrix(self):
        """
        Calculates Pearson correlation coefficients ($r$) between real numerical variables:
        - Project Budget
        - Total Amount Collected (Paid)
        - Project Progress (%)
        - Duration in Days
        - Associated Task Count
        """
        sample_rows = []
        for p in self.projects_qs:
            paid_sum = self.payments_qs.filter(project=p, status='paid').aggregate(t=Sum('amount'))['t'] or 0
            duration = (p.deadline - p.start_date).days if (p.start_date and p.deadline) else 0
            task_cnt = self.tasks_qs.filter(project=p).count()
            sample_rows.append({
                'budget': to_float(p.budget),
                'paid': to_float(paid_sum),
                'progress': float(p.progress),
                'duration': float(max(0, duration)),
                'tasks': float(task_cnt)
            })

        n = len(sample_rows)
        variables = ['budget', 'paid', 'progress', 'duration', 'tasks']
        var_labels = {
            'budget': 'Budget ($)',
            'paid': 'Revenue Collected ($)',
            'progress': 'Progress (%)',
            'duration': 'Duration (Days)',
            'tasks': 'Task Count'
        }

        if n < 3:
            return {
                'is_sufficient': False,
                'message': 'Correlation analysis requires at least 3 project records with numerical data.',
                'variables': [var_labels[v] for v in variables],
                'matrix': []
            }

        def pearson_r(x_list, y_list):
            mean_x = sum(x_list) / n
            mean_y = sum(y_list) / n
            cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_list, y_list))
            var_x = sum((x - mean_x) ** 2 for x in x_list)
            var_y = sum((y - mean_y) ** 2 for y in y_list)
            denominator = math.sqrt(var_x * var_y)
            if denominator < 1e-9:
                return 0.0
            return round(cov / denominator, 3)

        matrix = []
        relationships = []

        for i, var_x in enumerate(variables):
            row = []
            x_vals = [r[var_x] for r in sample_rows]
            for j, var_y in enumerate(variables):
                if i == j:
                    row.append(1.0)
                else:
                    y_vals = [r[var_y] for r in sample_rows]
                    r_val = pearson_r(x_vals, y_vals)
                    row.append(r_val)

                    # Only record upper triangle relationships
                    if i < j:
                        strength = 'None / Negligible'
                        abs_r = abs(r_val)
                        if abs_r >= 0.7:
                            strength = 'Strong'
                        elif abs_r >= 0.4:
                            strength = 'Moderate'
                        elif abs_r >= 0.2:
                            strength = 'Weak'

                        direction = 'Positive' if r_val > 0 else 'Negative'
                        relationships.append({
                            'var1': var_labels[var_x],
                            'var2': var_labels[var_y],
                            'r': r_val,
                            'direction': direction,
                            'strength': strength,
                            'interpretation': f"{strength} {direction} association (r = {r_val}). Note: Statistical correlation indicates co-movement but does not prove causation."
                        })
            matrix.append(row)

        return {
            'is_sufficient': True,
            'sample_size': n,
            'variables': [var_labels[v] for v in variables],
            'matrix': matrix,
            'relationships': relationships
        }

    # --------------------------------------------------------------------------
    # Phase 12: Outlier Detection Engine (IQR + Z-Score)
    # --------------------------------------------------------------------------
    def detect_outliers(self):
        """
        Detects statistical anomalies using both Interquartile Range (IQR)
        and Z-Score criteria across Budgets, Payments, and Task durations.
        """
        outliers = []

        # 1. Project Budgets Outliers
        projects_with_budget = [p for p in self.projects_qs if p.budget is not None]
        budgets = [to_float(p.budget) for p in projects_with_budget]

        if len(budgets) >= 4:
            sorted_b = sorted(budgets)
            q1 = compute_percentile(sorted_b, 25)
            q3 = compute_percentile(sorted_b, 75)
            iqr = q3 - q1
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)

            mean_b = sum(budgets) / len(budgets)
            std_b = math.sqrt(sum((x - mean_b) ** 2 for x in budgets) / len(budgets)) or 1.0

            for p in projects_with_budget:
                val = to_float(p.budget)
                z_score = (val - mean_b) / std_b
                is_iqr_outlier = val < lower_bound or val > upper_bound
                is_z_outlier = abs(z_score) >= 2.2

                if is_iqr_outlier or is_z_outlier:
                    method_used = 'IQR & Z-Score' if (is_iqr_outlier and is_z_outlier) else ('IQR Rule' if is_iqr_outlier else 'Z-Score (|z| > 2.2)')
                    outliers.append({
                        'dataset': 'Projects',
                        'item_name': p.name,
                        'client': p.client.name if p.client else 'N/A',
                        'variable': 'Budget',
                        'value': f"${val:,.2f}",
                        'benchmark': f"IQR Normal: [${max(0, lower_bound):,.0f} - ${upper_bound:,.0f}]",
                        'z_score': round(z_score, 2),
                        'method': method_used,
                        'explanation': f"Project value (${val:,.0f}) significantly departs from your average budget (${mean_b:,.0f}). Consider breaking into distinct deliverables or milestone-based payments."
                    })

        # 2. Payment Amount Outliers
        payments_list = list(self.payments_qs)
        pm_amounts = [to_float(pm.amount) for pm in payments_list]
        if len(pm_amounts) >= 4:
            sorted_pm = sorted(pm_amounts)
            q1 = compute_percentile(sorted_pm, 25)
            q3 = compute_percentile(sorted_pm, 75)
            iqr = q3 - q1
            upper_bound = q3 + (1.5 * iqr)
            mean_pm = sum(pm_amounts) / len(pm_amounts)
            std_pm = math.sqrt(sum((x - mean_pm) ** 2 for x in pm_amounts) / len(pm_amounts)) or 1.0

            for pm in payments_list:
                val = to_float(pm.amount)
                z_score = (val - mean_pm) / std_pm
                if val > upper_bound or z_score >= 2.2:
                    outliers.append({
                        'dataset': 'Payments',
                        'item_name': f"Payment for {pm.project.name if pm.project else 'Invoice'}",
                        'client': pm.project.client.name if (pm.project and pm.project.client) else 'N/A',
                        'variable': 'Payment Amount',
                        'value': f"${val:,.2f}",
                        'benchmark': f"Typical Max: ${upper_bound:,.0f}",
                        'z_score': round(z_score, 2),
                        'method': 'IQR & Z-Score',
                        'explanation': f"High-magnitude transaction representing {round((val/sum(pm_amounts))*100, 1)}% of total payment volume."
                    })

        return {
            'outliers': outliers,
            'count': len(outliers),
            'has_outliers': len(outliers) > 0
        }

    # --------------------------------------------------------------------------
    # Phase 13: Trend Trajectory & Growth Analysis
    # --------------------------------------------------------------------------
    def analyze_trends(self):
        """
        Performs historical time-series aggregation across the last 6 calendar months:
        - Monthly Revenue Trajectory
        - Monthly New Projects Started
        - Month-over-Month (% MoM) Growth Rates
        - Trajectory Classification (Growth / Decline / Stable)
        """
        months_labels = []
        monthly_revenue = []
        monthly_projects = []
        monthly_expenses = []

        for i in range(5, -1, -1):
            m_offset = (self.today.month - 1 - i) % 12 + 1
            y_offset = self.today.year + ((self.today.month - 1 - i) // 12)

            m_pay = float(self.payments_qs.filter(
                status='paid'
            ).filter(
                Q(paid_date__year=y_offset, paid_date__month=m_offset) |
                Q(paid_date__isnull=True, created_at__year=y_offset, created_at__month=m_offset)
            ).aggregate(t=Sum('amount'))['t'] or 0)

            m_inc = float(self.incomes_qs.filter(
                date__year=y_offset,
                date__month=m_offset
            ).aggregate(t=Sum('amount'))['t'] or 0)

            m_exp = float(self.expenses_qs.filter(
                date__year=y_offset,
                date__month=m_offset
            ).aggregate(t=Sum('amount'))['t'] or 0)

            p_count = self.projects_qs.filter(
                created_at__year=y_offset,
                created_at__month=m_offset
            ).count()

            m_date = date(y_offset, m_offset, 1)
            months_labels.append(m_date.strftime("%b %Y"))
            monthly_revenue.append(m_pay + m_inc)
            monthly_projects.append(p_count)
            monthly_expenses.append(m_exp)

        # Calculate MoM growth for the last 2 months
        curr_rev = monthly_revenue[-1]
        prev_rev = monthly_revenue[-2] if len(monthly_revenue) >= 2 else 0.0

        if prev_rev > 0:
            mom_rev_pct = round(((curr_rev - prev_rev) / prev_rev) * 100.0, 1)
            if mom_rev_pct > 5.0:
                trend_status = 'Upward Growth'
                trend_color = 'success'
                trend_icon = 'fa-arrow-trend-up'
            elif mom_rev_pct < -5.0:
                trend_status = 'Contracting / Decline'
                trend_color = 'danger'
                trend_icon = 'fa-arrow-trend-down'
            else:
                trend_status = 'Stable / Steady'
                trend_color = 'primary'
                trend_icon = 'fa-arrow-right'
        else:
            mom_rev_pct = 0.0
            trend_status = 'Baseline Period'
            trend_color = 'info'
            trend_icon = 'fa-minus'

        # Identify peak and lowest month
        peak_val = max(monthly_revenue) if monthly_revenue else 0.0
        peak_idx = monthly_revenue.index(peak_val) if monthly_revenue else 0
        peak_month = months_labels[peak_idx] if months_labels else 'N/A'

        return {
            'months': months_labels,
            'revenue_series': monthly_revenue,
            'projects_series': monthly_projects,
            'expenses_series': monthly_expenses,
            'current_month_revenue': curr_rev,
            'previous_month_revenue': prev_rev,
            'mom_growth_pct': mom_rev_pct,
            'trend_status': trend_status,
            'trend_color': trend_color,
            'trend_icon': trend_icon,
            'peak_month': peak_month,
            'peak_revenue': peak_val,
        }

    # --------------------------------------------------------------------------
    # Phase 14 & 15: Algorithmic Business Insights & Data-Driven Recommendations
    # --------------------------------------------------------------------------
    def generate_insights_and_recommendations(self):
        """
        Generates genuine data-driven insights and prescriptive recommendations
        derived strictly from the user's live database metrics.
        """
        insights = []
        recommendations = []

        total_projects = self.projects_qs.count()
        completed_p = self.projects_qs.filter(status='completed').count()
        active_p = self.projects_qs.filter(status='in_progress').count()

        total_paid = float(self.payments_qs.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0)
        total_pending = float(self.payments_qs.filter(status='pending').aggregate(t=Sum('amount'))['t'] or 0)
        overdue_pending = float(self.payments_qs.filter(status='pending', due_date__lt=self.today).aggregate(t=Sum('amount'))['t'] or 0)

        # 1. Revenue & Client Concentration Insight
        if total_paid > 0:
            client_earnings = {}
            for pm in self.payments_qs.filter(status='paid'):
                c_name = pm.project.client.name if (pm.project and pm.project.client) else 'Independent'
                client_earnings[c_name] = client_earnings.get(c_name, 0.0) + to_float(pm.amount)

            if client_earnings:
                top_client, top_val = max(client_earnings.items(), key=lambda x: x[1])
                concentration_pct = round((top_val / total_paid) * 100.0, 1)

                insights.append({
                    'category': 'Client Revenue Concentration',
                    'icon': 'fa-users',
                    'title': f'Key Client Reliance: {top_client}',
                    'text': f'"{top_client}" generates ${top_val:,.2f}, representing {concentration_pct}% of your total realized revenue.',
                    'badge': f'{concentration_pct}% Revenue Share',
                    'badge_type': 'warning' if concentration_pct > 60 else 'info'
                })

                if concentration_pct > 60:
                    recommendations.append({
                        'priority': 'High Priority',
                        'priority_class': 'danger',
                        'title': 'Diversify Client Portfolio',
                        'action': f'Over 60% of your earnings depend on a single client ({top_client}). Acquire 1-2 new recurring clients to mitigate cashflow risk.'
                    })

        # 2. Cashflow & Overdue Payment Insight
        if total_pending > 0:
            pending_ratio = round((total_pending / (total_paid + total_pending)) * 100.0, 1)
            insights.append({
                'category': 'Cashflow Health',
                'icon': 'fa-wallet',
                'title': f'Outstanding Accounts Receivable: ${total_pending:,.2f}',
                'text': f'{pending_ratio}% of your total invoiced business value remains uncollected in pending status.',
                'badge': f'${total_pending:,.0f} Pending',
                'badge_type': 'warning'
            })

            if overdue_pending > 0:
                recommendations.append({
                    'priority': 'Urgent',
                    'priority_class': 'danger',
                    'title': f'Resolve ${overdue_pending:,.2f} in Overdue Invoices',
                    'action': 'Automated or manual follow-ups should be issued for past-due payments to prevent delayed operational cashflow.'
                })

        # 3. Delivery & Completion Velocity Insight
        if total_projects > 0:
            comp_rate = round((completed_p / total_projects) * 100.0, 1)
            insights.append({
                'category': 'Project Execution',
                'icon': 'fa-diagram-project',
                'title': f'Portfolio Completion Rate: {comp_rate}%',
                'text': f'You have successfully completed {completed_p} of {total_projects} total managed projects ({active_p} currently in active delivery).',
                'badge': f'{comp_rate}% Completion',
                'badge_type': 'success' if comp_rate >= 50 else 'secondary'
            })

            if active_p > 5:
                recommendations.append({
                    'priority': 'Medium',
                    'priority_class': 'warning',
                    'title': 'Balance Work-in-Progress (WIP) Limits',
                    'action': f'You currently have {active_p} simultaneous active projects. Consider establishing a WIP limit of 3-4 projects to maximize delivery focus.'
                })

        # Fallback if brand new account with 0 data
        if not insights:
            insights.append({
                'category': 'Platform Readiness',
                'icon': 'fa-circle-info',
                'title': 'Awaiting Initial Business Activity',
                'text': 'Log clients, projects, and payment transactions to unlock automated intelligence profiling and trend calculations.',
                'badge': 'Ready to Analyze',
                'badge_type': 'info'
            })
            recommendations.append({
                'priority': 'Getting Started',
                'priority_class': 'info',
                'title': 'Create Your First Client & Project',
                'action': 'Begin by logging active contracts and project milestones to enable deep analytical dashboards.'
            })

        return {
            'insights': insights,
            'recommendations': recommendations
        }

    # --------------------------------------------------------------------------
    # Phase 10: Interactive Drill-Down Engine
    # --------------------------------------------------------------------------
    def get_drilldown_data(self, dimension, value):
        """
        Retrieves underlying raw records when a user clicks on any chart slice/dimension.
        Dimensions: 'client', 'status', 'month', 'priority'.
        """
        records = []
        title = f"Drill-down: {dimension.capitalize()} = '{value}'"

        if dimension == 'client':
            p_list = self.projects_qs.filter(client__name__iexact=value)
            for p in p_list:
                paid = self.payments_qs.filter(project=p, status='paid').aggregate(t=Sum('amount'))['t'] or 0
                records.append({
                    'id': str(p.id),
                    'name': p.name,
                    'client': p.client.name,
                    'status': p.get_status_display(),
                    'budget': f"${to_float(p.budget):,.2f}",
                    'paid': f"${to_float(paid):,.2f}",
                    'progress': f"{p.progress}%",
                    'deadline': p.deadline.isoformat() if p.deadline else '—'
                })

        elif dimension == 'status':
            p_list = self.projects_qs.filter(status=value)
            for p in p_list:
                records.append({
                    'id': str(p.id),
                    'name': p.name,
                    'client': p.client.name if p.client else 'N/A',
                    'status': p.get_status_display(),
                    'budget': f"${to_float(p.budget):,.2f}",
                    'progress': f"{p.progress}%",
                    'deadline': p.deadline.isoformat() if p.deadline else '—'
                })

        elif dimension == 'payment_status':
            pm_list = self.payments_qs.filter(status=value)
            for pm in pm_list:
                records.append({
                    'id': str(pm.id),
                    'project': pm.project.name if pm.project else 'N/A',
                    'client': pm.project.client.name if (pm.project and pm.project.client) else 'N/A',
                    'amount': f"${to_float(pm.amount):,.2f}",
                    'status': pm.get_status_display(),
                    'due_date': pm.due_date.isoformat() if pm.due_date else '—'
                })

        return {
            'title': title,
            'dimension': dimension,
            'value': value,
            'count': len(records),
            'records': records
        }

    # --------------------------------------------------------------------------
    # Phase 16: Safe 1-Click Data Cleaning Actions
    # --------------------------------------------------------------------------
    def apply_safe_clean_action(self, action_type):
        """
        Executes a safe, non-destructive data normalization action.
        Returns a result dict with 'success' bool and 'message' string.
        """
        if action_type == 'sync_completed_status':
            updated = self.projects_qs.filter(progress=100).exclude(status='completed').update(status='completed')
            return {
                'success': True,
                'message': f'Synchronized {updated} project(s) with 100% progress to "Completed" status.'
            }

        if action_type == 'mark_overdue_payments':
            overdue_qs = self.payments_qs.filter(status='pending', due_date__lt=self.today)
            count = overdue_qs.count()
            if count == 0:
                return {'success': False, 'message': 'No overdue pending payments found to update.'}
            return {
                'success': True,
                'message': f'Flagged {count} overdue payment(s) for follow-up. Please review and mark as needed.'
            }

        return {
            'success': False,
            'message': f'Unknown clean action: "{action_type}". No changes were made.'
        }
