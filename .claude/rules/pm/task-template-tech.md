# Task Template - Technical Details

> **Frontend and backend technical details template (for all tech stacks)**
>
> **Example stacks**: Frontend (React/Flutter/Vue/Angular), Backend (Go/Node.js/Python/Java)

---

## Technical Details Section Structure

```markdown
## Technical Details

### Implementation Plan
[Implementation steps]

### Frontend (if applicable)
#### Component Structure
[Component tree]

#### State Management
[State solution]

#### Routing
[Route config]

#### UI/UX Specifications
[UI specs]

### Backend (if applicable)
#### API Specifications
[API endpoints]

#### Database Design
[DB tables]

#### Data Model
[Go Struct / TS Interface]

#### Business Logic
[Business logic]

### Common
#### Performance Optimization
[Performance]

#### Testing Strategy
[Testing]
```

---

## 1. Implementation Plan

**Format**:
```markdown
### Implementation Plan

**Phase 1: [Phase name]**
1. Step 1
2. Step 2

**Phase 2: [Phase name]**
1. Step 1
2. Step 2
```

**Examples**:
- Frontend: Phase 1 Component dev → Phase 2 State integration → Phase 3 API integration
- Backend: Phase 1 Data model → Phase 2 API dev → Phase 3 Test & optimize

---

## 2. Component Structure (Frontend)

### React

```markdown
#### Component Hierarchy
PageName/
├── ComponentA (new)
│   ├── SubComponent1
│   └── SubComponent2
├── ComponentB (modify)
└── ComponentC (reuse)

#### Component Responsibilities
- ComponentA: Responsibility description
- ComponentB: Responsibility description

#### Props Definition
interface ComponentAProps {
  prop1: string;
  prop2: number;
  onAction: () => void;
}
```

### Flutter

```markdown
#### Widget Hierarchy
ScreenName/
├── WidgetA (new)
│   └── SubWidget
├── WidgetB (modify)
└── WidgetC (reuse)

#### Props Definition
class WidgetA extends StatelessWidget {
  final String prop1;
  final VoidCallback onAction;

  const WidgetA({required this.prop1, required this.onAction});
}
```

---

## 3. State Management (Frontend)

### Redux Toolkit (React)

```markdown
**State Slice**: `xxxSlice.ts`

interface XxxState {
  items: Item[];
  loading: boolean;
  error: string | null;
}

**Actions**: fetchItems(), setFilters()
**Selectors**: selectFilteredItems, selectIsLoading
```

### Zustand (React)

```markdown
**Store**: `useXxxStore.ts`

interface XxxStore {
  items: Item[];
  loading: boolean;
  fetchItems: () => Promise<void>;
}
```

### Riverpod (Flutter)

```markdown
**Providers**:

final itemListProvider = StateNotifierProvider<ItemListNotifier, AsyncValue<List<Item>>>((ref) {
  return ItemListNotifier(ref.read(repositoryProvider));
});
```

### Bloc (Flutter)

```markdown
**Events**: LoadItems, FilterItems
**States**: ItemInitial, ItemLoading, ItemLoaded, ItemError
**Bloc**: ItemBloc
```

---

## 4. Routing (Frontend)

### React Router

```markdown
**New Route**:
{
  path: '/xxx',
  element: <XxxPage />,
  children: [...]
}

**Navigation**: `navigate('/xxx/:id')`
```

### Go Router (Flutter)

```markdown
**Config**:
GoRoute(
  path: '/xxx',
  builder: (context, state) => XxxScreen(),
)

**Navigation**: `context.go('/xxx/:id')`
```

---

## 5. UI/UX Specifications (Frontend)

```markdown
### UI/UX Specifications

#### Design Tokens
**Colors**: Primary #1890ff, Success #52c41a, Error #ff4d4f
**Typography**: Title 24px/32px, Body 14px/22px
**Spacing**: XS 4px, S 8px, M 16px, L 24px

#### Component Specs
**SearchBar**: Height 40px, Border radius 8px, Padding 8px 16px
**Card**: Padding 16px, Border radius 8px, Shadow 0 2px 8px

#### Animations
**Loading**: 1.5s ease-in-out
**Hover**: 200ms scale 1.02

#### Responsive Breakpoints
- Mobile: < 768px (single column)
- Tablet: 768px-1024px (two columns)
- Desktop: > 1024px (three columns + sidebar)
```

---

## 6. API Specifications (Backend)

### Endpoint Definition

```markdown
#### Endpoint: [Name]

**Basic Info**:
- Method: GET/POST/PUT/DELETE
- Path: /api/v1/xxx
- Auth: Required (Bearer Token)
- Permission: xxx:read / xxx:write

**Request Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| page | int | No | Page number (default 1) |
| pageSize | int | No | Items per page (default 20) |

**Request Example**:
GET /api/v1/xxx?page=1
Authorization: Bearer <token>

**Response (200)**:
{
  "code": 0,
  "message": "success",
  "data": {...}
}

**Response Errors**:
- 401: Unauthorized
- 400: Bad request
- 404: Not found
- 500: Server error

**Rate Limiting**: 100 requests/minute/user
**Caching**: Redis 5 min TTL
```

---

## 7. Database Design (Backend)

```markdown
### Database Design

#### Table: `table_name`

**DDL**:
CREATE TABLE `table_name` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `field1` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_field1` (`field1`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

**Index Strategy**:
- uk_field1: Unique index
- idx_created_at: Time range queries

**Relations**:
- field_id → other_table.id (Many-to-One)
```

---

## 8. Data Model

### Go Struct (Backend)

```markdown
**File**: `models/xxx.go`

type Xxx struct {
    Id        int64     `orm:"pk;auto" json:"id"`
    Field1    string    `orm:"size(100)" json:"field1" valid:"Required"`
    CreatedAt time.Time `orm:"auto_now_add" json:"createdAt"`
}
```

### TypeScript Interface (Frontend)

```markdown
**File**: `types/xxx.ts`

interface Xxx {
  id: number;
  field1: string;
  createdAt: string;
}
```

---

## 9. Business Logic (Backend)

```markdown
### Business Logic

**Service Layer**: `services/xxx_service.go`

**Core Logic**:
1. Cache strategy: Check cache first, query DB if miss, write to cache (TTL 5 min)
2. Permission check: Users can only operate their own resources
3. Concurrency control: Redis distributed lock prevents duplicate operations

**Key Functions**:
- GetList(): Get list (with cache)
- Create(): Create resource (clear cache)
- Update(): Update resource (clear cache)
```

---

## 10. Performance Optimization

### Frontend Performance

```markdown
### Performance Optimization

#### Bundle Optimization
- Code Splitting: Lazy load by route
- Tree Shaking: Use ES Modules
- Bundle Size: < 200KB per chunk

#### Rendering Optimization
- React.memo / const: Reduce re-renders
- useMemo / useCallback: Cache computations and functions
- Virtualization: Use virtual scrolling for lists > 50 items

#### Network Optimization
- Debounce: Search input debounce 300ms
- Caching: TanStack Query cache (5 min)
- Pagination: 20 items per page

#### Performance Metrics
- LCP < 2.5s
- FID < 100ms
- CLS < 0.1
```

### Backend Performance

```markdown
### Performance Optimization

#### Database Optimization
- Index optimization: Add indexes for frequent queries
- Pagination: LIMIT + OFFSET
- Query optimization: Query only needed fields

#### Cache Strategy
- Redis cache: Lists 5 min, details 10 min
- Cache invalidation: Active cleanup after update/delete
- Cache penetration: Cache empty results (TTL 1 min)

#### Concurrency Optimization
- Goroutine Pool: Batch operations
- Context timeout: Set timeout for DB operations
- Distributed lock: Redis lock prevents race conditions

#### Performance Metrics
- Response time P95 < 200ms
- Throughput > 1000 QPS
- Cache hit rate > 85%
```

---

## 11. Testing Strategy

### Frontend Testing

```markdown
### Testing Strategy

#### Unit Tests
- Component rendering tests
- Props passing tests
- Event handling tests
- State management tests

**Tools**: React Testing Library / Flutter Test

#### Integration Tests
- User flow tests (end-to-end)
- API integration tests

**Tools**: Playwright / Cypress / Flutter Integration Test

#### Visual Regression
- Key page screenshot comparison

**Tools**: Percy / Chromatic
```

### Backend Testing

```markdown
### Testing Strategy

#### Unit Tests
- Service layer business logic
- Parameter validation logic
- Utility functions

**Coverage**: ≥ 90%

#### Integration Tests
- API endpoint tests
- Database operation tests
- Cache logic tests

#### Load Tests
- Tool: wrk
- Target: QPS > 1000, P99 < 500ms
```

---

## 12. Definition of Done (Additional Standards)

### Frontend DoD

```markdown
#### UI Completeness
- [ ] 100% design spec restoration (error ≤ 2px)
- [ ] All interaction states (Hover/Active/Disabled/Loading)
- [ ] Empty state pages

#### Responsive
- [ ] Mobile tested (< 768px)
- [ ] Tablet tested (768px-1024px)
- [ ] Desktop tested (> 1024px)

#### Cross-browser/platform
- [ ] Chrome / Firefox / Safari (Web)
- [ ] iOS / Android (Flutter)

#### Performance
- [ ] Lighthouse ≥ 90
- [ ] Bundle size within budget

#### Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader tested
- [ ] Color contrast meets WCAG 2.1 AA
```

### Backend DoD

```markdown
#### API Completeness
- [ ] All endpoints implemented
- [ ] Complete parameter validation
- [ ] Error handling covered
- [ ] Standard response format

#### Database
- [ ] Tables created
- [ ] Indexes optimized
- [ ] Migration scripts rollbackable

#### Security
- [ ] Authentication/authorization correct
- [ ] No input validation gaps
- [ ] SQL injection protected
- [ ] Sensitive data encrypted

#### Performance
- [ ] Response time meets target (P95 < 200ms)
- [ ] Cache strategy implemented
- [ ] Database queries optimized
- [ ] Load tests passed (QPS > 1000)

#### Docs
- [ ] API docs updated
- [ ] Schema docs
```

---

## 13. Usage Recommendations

### Frontend Tasks Priority

- Component Structure
- State Management
- UI/UX Specifications
- Routing
- Performance (Frontend)
- Testing (Frontend)

### Backend Tasks Priority

- API Specifications
- Database Design
- Data Model
- Business Logic
- Performance (Backend)
- Testing (Backend)

### Fullstack Tasks

Fill both parts, describe frontend and backend technical details separately.

---

## 14. Related Rules

- **Common structure**: `task-template-common.md`
- **Decomposition**: `core-principles.md`
- **Timestamps**: `datetime.md`

---

**Note**: When executing this rule, AI should generate task files in Chinese for team collaboration.
