# Database Design - Freelancer Project Tracker

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User (Django Auth)                      │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)                                                         │
│ username                                                        │
│ email                                                           │
│ password (hashed)                                                │
│ first_name                                                      │
│ last_name                                                       │
│ is_active                                                       │
│ is_staff                                                        │
│ is_superuser                                                    │
└─────────────────────────────────────────────────────────────────┘
         │
         │ 1:N
         │
         ├───────────────────────────────────────────────────────────┐
         │                                                           │
         ▼                                                           ▼
┌─────────────────────────────────┐              ┌─────────────────────────────────┐
│           Client                │              │           Project                │
├─────────────────────────────────┤              ├─────────────────────────────────┤
│ id (PK, UUID)                   │              │ id (PK, UUID)                   │
│ user (FK)                       │              │ user (FK)                       │
│ name                            │              │ client (FK)                     │
│ email                           │              │ name                            │
│ phone                           │              │ description                     │
│ company                         │              │ status                          │
│ address                         │              │ priority                        │
│ status                          │              │ start_date                      │
│ notes                           │              │ deadline                        │
│ created_at                      │              │ budget                          │
│ updated_at                      │              │ progress                        │
└─────────────────────────────────┘              │ created_at                      │
         │                                        │ updated_at                      │
         │ 1:N                                    └─────────────────────────────────┘
         │                                                 │
         │                                                 │ 1:N
         │                                                 │
         ▼                                                 ▼
┌─────────────────────────────────┐              ┌─────────────────────────────────┐
│           Note                   │              │           Payment               │
├─────────────────────────────────┤              ├─────────────────────────────────┤
│ id (PK, UUID)                   │              │ id (PK, UUID)                   │
│ user (FK)                       │              │ user (FK)                       │
│ project (FK, nullable)          │              │ project (FK)                    │
│ client (FK, nullable)           │              │ amount                          │
│ title                           │              │ status                          │
│ content                         │              │ payment_method                  │
│ is_private                      │              │ due_date                        │
│ created_at                      │              │ paid_date                       │
│ updated_at                      │              │ description                     │
└─────────────────────────────────┘              │ invoice_number                  │
                                                  │ created_at                      │
                                                  │ updated_at                      │
                                                  └─────────────────────────────────┘
                                                           │
                                                           │ 1:N
                                                           │
                                                           ▼
                                                  ┌─────────────────────────────────┐
                                                  │            Task                  │
                                                  ├─────────────────────────────────┤
                                                  │ id (PK, UUID)                   │
                                                  │ user (FK)                       │
                                                  │ project (FK)                    │
                                                  │ title                           │
                                                  │ description                     │
                                                  │ status                          │
                                                  │ priority                        │
                                                  │ due_date                        │
                                                  │ estimated_hours                 │
                                                  │ actual_hours                    │
                                                  │ created_at                      │
                                                  │ updated_at                      │
                                                  └─────────────────────────────────┘

┌─────────────────────────────────┐
│        ActivityLog              │
├─────────────────────────────────┤
│ id (PK, UUID)                   │
│ user (FK)                       │
│ action                          │
│ model_type                      │
│ model_id                        │
│ description                     │
│ timestamp                       │
│ ip_address                      │
└─────────────────────────────────┘
```

## Model Relationships

### User (Django Auth)
- **One-to-Many with Client**: One user can have multiple clients
- **One-to-Many with Project**: One user can have multiple projects
- **One-to-Many with Payment**: One user can have multiple payments
- **One-to-Many with Task**: One user can have multiple tasks
- **One-to-Many with Note**: One user can have multiple notes
- **One-to-Many with ActivityLog**: One user can have multiple activity logs

### Client
- **Many-to-One with User**: Multiple clients belong to one user
- **One-to-Many with Project**: One client can have multiple projects
- **One-to-Many with Note**: One client can have multiple notes (via client_notes)

### Project
- **Many-to-One with User**: Multiple projects belong to one user
- **Many-to-One with Client**: Multiple projects belong to one client
- **One-to-Many with Payment**: One project can have multiple payments
- **One-to-Many with Task**: One project can have multiple tasks
- **One-to-Many with Note**: One project can have multiple notes (via project_notes)

### Payment
- **Many-to-One with User**: Multiple payments belong to one user
- **Many-to-One with Project**: Multiple payments belong to one project

### Task
- **Many-to-One with User**: Multiple tasks belong to one user
- **Many-to-One with Project**: Multiple tasks belong to one project

### Note
- **Many-to-One with User**: Multiple notes belong to one user
- **Many-to-One with Project**: Notes can be associated with a project (optional)
- **Many-to-One with Client**: Notes can be associated with a client (optional)

### ActivityLog
- **Many-to-One with User**: Multiple activity logs belong to one user

## Model Details

### Client Model
- **Purpose**: Store client information for the freelancer
- **Key Fields**: name, email, phone, company, address, status
- **Status Options**: active, inactive, prospective
- **Methods**: get_total_projects(), get_total_payments()

### Project Model
- **Purpose**: Track projects for each client
- **Key Fields**: name, description, status, priority, start_date, deadline, budget, progress
- **Status Options**: pending, in_progress, completed, on_hold, cancelled
- **Priority Options**: low, medium, high, urgent
- **Methods**: get_total_tasks(), get_completed_tasks(), get_total_payments(), get_pending_payments(), is_overdue()

### Payment Model
- **Purpose**: Track payments for projects
- **Key Fields**: project, amount, status, payment_method, due_date, paid_date, invoice_number
- **Status Options**: pending, paid, overdue, cancelled
- **Payment Methods**: bank_transfer, paypal, stripe, cash, check, other
- **Methods**: is_overdue()

### Task Model
- **Purpose**: Track individual tasks within projects
- **Key Fields**: project, title, description, status, priority, due_date, estimated_hours, actual_hours
- **Status Options**: todo, in_progress, completed, cancelled
- **Priority Options**: low, medium, high, urgent
- **Methods**: is_overdue()

### Note Model
- **Purpose**: Store notes related to projects or clients
- **Key Fields**: project (optional), client (optional), title, content, is_private
- **Flexibility**: Can be associated with either a project or a client
- **Methods**: get_related_object()

### ActivityLog Model
- **Purpose**: Track user actions for audit trail
- **Key Fields**: user, action, model_type, model_id, description, timestamp, ip_address
- **Action Types**: create, update, delete, login, logout, status_change, payment_received
- **Model Types**: client, project, payment, task, note, user
- **Constraints**: Read-only in admin (manual creation/editing prevented)

## Database Constraints

### Primary Keys
- All models use UUID primary keys for better security and distribution

### Foreign Keys
- All foreign keys have CASCADE delete for simplicity
- User foreign keys ensure data isolation between users

### Field Constraints
- Email validation for email fields
- Regex validation for numeric fields (progress)
- Decimal precision for financial fields (amount, budget, hours)

### Indexing
- Automatic indexes on foreign keys
- Additional indexes via Meta ordering for performance

## Migration Strategy

### Development
- SQLite database for development
- Easy migration using Django's built-in migration system

### Production
- PostgreSQL for production scalability
- Uncomment psycopg2-binary in requirements.txt
- Update DATABASES setting in settings.py
- Run migrations on production database

## Data Flow

1. **User Registration**: Creates Django User instance
2. **Client Creation**: Links to User, creates Client instance
3. **Project Creation**: Links to User and Client, creates Project instance
4. **Task Creation**: Links to User and Project, creates Task instance
5. **Payment Tracking**: Links to User and Project, creates Payment instance
6. **Note Creation**: Links to User and optionally Project/Client
7. **Activity Logging**: Automatic logging of all CRUD operations