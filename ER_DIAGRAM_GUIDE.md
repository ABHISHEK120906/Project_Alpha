# Entity Relationship Diagram Guide

## ER Diagram Visualization

The ER diagram for the Freelancer Project Tracker System is provided in `er_diagram.mmd` format using Mermaid syntax.

## How to View the ER Diagram

### Option 1: Online Mermaid Editor
1. Visit [Mermaid Live Editor](https://mermaid.live/)
2. Copy the contents of `er_diagram.mmd`
3. Paste into the editor
4. The diagram will render automatically

### Option 2: GitHub/GitLab
- If you push this file to GitHub or GitLab, the diagram will render automatically in the repository viewer

### Option 3: VS Code Extension
1. Install the "Mermaid Preview" extension in VS Code
2. Open `er_diagram.mmd`
3. Right-click and select "Mermaid: Open Preview"

### Option 4: Command Line
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate PNG
mmdc -i er_diagram.mmd -o er_diagram.png

# Generate SVG
mmdc -i er_diagram.mmd -o er_diagram.svg
```

## Entity Relationships Summary

### Core Relationships
- **User** is the central entity, linked to all other entities
- **Client** belongs to a User and has multiple Projects
- **Project** belongs to a User and Client, contains Tasks, Payments, and Notes
- **Task** belongs to a User and Project
- **Payment** belongs to a User and Project
- **Note** belongs to a User and optionally a Project or Client
- **ActivityLog** belongs to a User and tracks all actions

### Key Relationships
1. **User → Client**: One-to-Many (A freelancer can have multiple clients)
2. **User → Project**: One-to-Many (A freelancer can have multiple projects)
3. **Client → Project**: One-to-Many (A client can have multiple projects)
4. **Project → Task**: One-to-Many (A project can have multiple tasks)
5. **Project → Payment**: One-to-Many (A project can have multiple payments)
6. **Project → Note**: One-to-Many (A project can have multiple notes)
7. **Client → Note**: One-to-Many (A client can have multiple notes)

## Database Schema Highlights

### Primary Keys
- All tables use UUID primary keys for security and distributed system compatibility

### Foreign Keys
- All foreign keys reference User for data isolation
- Cascade delete is used for simplicity (can be changed to PROTECT if needed)

### Important Constraints
- Email validation on Client.email
- Numeric validation on Project.progress (0-100)
- Decimal precision on financial fields (12,2 for amounts, 5,2 for hours)
- Optional relationships (Note can be linked to Project OR Client, not both)

### Status Enums
- **Client**: active, inactive, prospective
- **Project**: pending, in_progress, completed, on_hold, cancelled
- **Payment**: pending, paid, overdue, cancelled
- **Task**: todo, in_progress, completed, cancelled

### Priority Levels
- **Project/Task**: low, medium, high, urgent

### Payment Methods
- bank_transfer, paypal, stripe, cash, check, other

## Normalization

The database follows Third Normal Form (3NF):
1. **1NF**: All fields are atomic, no repeating groups
2. **2NF**: All non-key attributes are fully dependent on the primary key
3. **3NF**: No transitive dependencies (all attributes depend only on the primary key)

## Performance Considerations

### Indexes
- Automatic indexes on all foreign keys
- Additional indexes via Meta ordering for common queries
- Consider adding composite indexes for complex queries

### Query Optimization
- Use select_related() for foreign key relationships
- Use prefetch_related() for many-to-many relationships
- Implement database-level pagination for large datasets

### Scalability
- UUID primary keys allow for easy horizontal scaling
- Database is designed to handle multi-tenant architecture via User foreign keys
- Ready for PostgreSQL migration for production workloads