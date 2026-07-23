# Analysis Sequence Diagram: Manage Assets

## Participants:
- **Actor**: User (executes the use case)
- **Boundary Class**: User Interface (handles user input)
- **Control Class**: Asset Manager (coordinates asset operations)
- **Entity Classes**: 
  - Resource (base resource class)
  - Organization (context for resources)
  - Warehouse (storage locations)
  - ResourceWarehouse (resource-warehouse mapping)

## Sequence Flow:

1. User initiates "Manage Assets" operation
2. User Interface receives request and validates input
3. Asset Manager (control) coordinates the operation
4. Asset Manager queries organization context
5. Asset Manager retrieves resource information
6. Asset Manager checks warehouse stock
7. Asset Manager updates resource-warehouse mapping
8. Asset Manager confirms operation and returns result

## Message Flow:
User → UI: Request to manage asset
UI → Asset Manager: Validate and process
Asset Manager → Organization: Resolve organization ID
Asset Manager → Resource: Query resource details
Asset Manager → Warehouse: Check available stock
Asset Manager → ResourceWarehouse: Update quantity
Asset Manager → UI: Return success/failure
UI → User: Display result

## Activation Periods:
- User: Activated for input duration
- UI: Activated during request processing
- Asset Manager: Activated during coordination
- Organization: Activated during ID resolution
- Resource: Activated during query
- Warehouse: Activated during stock check
- ResourceWarehouse: Activated during update