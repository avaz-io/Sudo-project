# Campusly — UI/UX Design

Design documentation for the **University Event Manager** web application, based on the project requirements dated 13 October 2026.

| Item | Details |
| --- | --- |
| UI/UX designer and tester | Avazbek Soibnazarov |
| Platform | Responsive website for laptop and mobile browsers |
| Design tool | Figma Design |
| Last updated | 21 October 2026 |
| Status | Initial screens and user flows prepared; interactive prototype and implementation validation pending |

## Figma file

[Open Campusly — University Event Manager](https://www.figma.com/design/i4SWRv03mNx6ZVdU0ksQlw/Campusly-University-Event-Manager)

The file contains three pages:

1. **Page 1** — light theme screens.
2. **Dark · Midnight & Gold** — dark theme screens with navy backgrounds and yellow accents.
3. **User Flows · Requirements** — visitor, student, and organizer flows, decision branches, and event status lifecycle.

The last editing session reported a Figma connection issue. Verify that all pages have synced before sharing or submitting the file.

## Design objective

Help students and staff discover university events and manage their registrations. Give authorized organizers a clear way to create, publish, edit, and cancel their events and view participants. Prioritize required midterm workflows, readable information, labelled forms, and consistent feedback.

## Users and access

| User | Available actions |
| --- | --- |
| Visitor | Browse published upcoming events, search by title, filter by category, view event details, sign up, and log in. |
| Standard user, labelled Student in the design | Register for eligible events, view My registrations, cancel eligible registrations, view their profile, update their display name, and log out. |
| Authorized organizer | Use standard-user functions and manage their own events and participant lists. |

New accounts receive the standard-user role. Organizer access is assigned through the project's documented setup procedure. Users cannot change their own role through profile editing. Organizer controls must be hidden from unauthorized users, and the backend must independently enforce permissions and event ownership.

## Screen inventory

Each theme includes the same 13 design screens. The last two are mobile-browser layouts, not native mobile applications.

| No. | Screen | Purpose |
| --- | --- | --- |
| 01 | Discover | Published upcoming events, title search, and category filtering. |
| 02 | Event details | Event information, organizer, status, availability, and registration action. |
| 03 | Log in | Email and password authentication. |
| 04 | Create account | Display name, unique email, and password. |
| 05 | My registrations | Registered events, event status, and cancellation entry points. |
| 06 | Profile | View account information and edit the display name. |
| 07 | My events | Organizer event overview and management entry points. |
| 08 | Create event | Enter event details, save a draft, or publish when valid. |
| 09 | Edit event | Update an owned event, publish an eligible draft, or cancel an eligible event. |
| 10 | Participants | Active participant names, registration dates, and count for an owned event. |
| 11 | Components and states | Palette examples, registration actions, and feedback references. |
| 12 | Mobile Discover | Event browsing at a 390 px design width. |
| 13 | Mobile event details | Event information and registration at a 390 px design width. |

## Main user flows

### Visitor and account

Discover → search or filter → event details → choose a protected action → log in or create an account → resume the intended action.

- Invalid input, duplicate email, or incorrect credentials must show a clear error and allow correction.
- The account menu provides Profile and Log out.
- Profile editing changes the display name; email and role are shown as read-only in the current design.
- Log out ends the authenticated session and returns the user to public browsing.

### Student registration

Event details → check eligibility → Register → confirmation → My registrations.

- Registration requires authentication, a published event that has not started, available capacity when limited, and no duplicate active registration.
- Show **Register**, **Cancel registration**, **Event full**, **Event cancelled**, **Registration closed**, or **Log in to register**, as appropriate.
- Cancelling an active registration is allowed before the event starts and releases its place.
- A previously cancelled registration may be reactivated if the event is still eligible.
- If the organizer cancels the event, My registrations must reflect the cancelled event status.
- An event without a capacity limit must be described as having no capacity limit.

### Organizer management

My events → Create event → enter details → Save draft → edit → validate → Publish → visible in Discover.

- Event fields: title, description, category, date, time, location, and optional participant capacity.
- A draft is visible only to its organizer.
- Publishing requires complete information and a future event date and time.
- The organizer can edit their own drafts and upcoming published events.
- A supplied capacity must be a positive integer and cannot be reduced below the active registration count.
- From an owned event, the organizer can view active participants and registration dates or cancel an eligible event.
- Manual completion after the scheduled time is sufficient for the midterm version.

### Event lifecycle

```text
Draft ----publish----> Published ----after scheduled time----> Completed
  |                        |
  +----cancel----> Cancelled <----cancel before start---------+
```

Registration records have a separate status: **active** or **cancelled**. Only active registrations count toward event capacity.

## Visual design

### Light palette

| Token | Colour |
| --- | --- |
| Primary accent | `#6941D9` |
| Main text | `#231E37` |
| Secondary text | `#817B90` |
| Page background | `#F8F7FB` |
| Surface | `#FFFFFF` |
| Border | `#DED9E8` |

### Dark palette — Midnight & Gold

| Token | Colour |
| --- | --- |
| Page background | `#0B1426` |
| Surface | `#14223A` |
| Elevated panel | `#1A2E4D` |
| Primary accent | `#F5CE57` |
| Main text | `#F2F5FC` |
| Secondary text | `#A9B7D0` |
| Border | `#354662` |

Use yellow mainly for primary actions, selected navigation, and highlights. Primary yellow buttons use dark text. Preserve separate success and error colours so status does not depend on the accent colour alone.

### Typography and layout

- Typeface: Inter, with Arial as a fallback in the SVG sources.
- Desktop screen width: 1440 px, with 64 px content margins.
- Mobile screen width: 390 px, with 20 px content margins.
- Main headings: approximately 32–36 px; section headings: 24 px; body: 14–16 px; labels: 12–13 px.
- Buttons: 46 px high; form fields: 50 px high.
- Cards: approximately 14–16 px corner radius.
- Event art uses original abstract vector illustrations. Event names, people, counts, dates, and other sample content are demonstration data.

## Requirement mapping

This table records where the requirement is represented or documented. It does not certify that the application has implemented or passed it.

| Requirement | Design coverage |
| --- | --- |
| FR-01 User registration | Create account; validation behaviour documented in the account flow. |
| FR-02 User login | Log in; protected-action entry and credential-error behaviour. |
| FR-03 User logout | Header/account navigation and user-flow documentation. |
| FR-04 User profile | Profile viewing, editable display name, read-only email and role. |
| FR-05 Discovery and search | Discover, title search, category selector, and mobile discovery. |
| FR-06 Event details | Details screens, event information, status, capacity, and registration state. |
| FR-07 Event creation | Create event, required fields, optional capacity, and draft behaviour. |
| FR-08 Event management | My events, Edit event, publishing and cancellation paths. |
| FR-09 Event registration | Details action, eligibility decisions, and registration state reference. |
| FR-10 Registration management | My registrations, cancellation and re-registration rules. |
| FR-11 Participant lists | Participants screen with names, dates, and active count. |
| FR-12 Event status | Status labels and user-flow lifecycle; manual completion is documented, with a dedicated control still to be detailed. |
| NFR-03 Usability | Consistent navigation, labelled forms, readable information, and mobile discovery/details examples. Remaining responsive screens and interaction accessibility need verification. |

## Feedback, accessibility, and frontend handoff

The frontend should provide:

- Inline field errors for invalid input and clear feedback for failed requests.
- Success feedback after registration, cancellation, and profile or event updates.
- Loading, empty-search, no-registrations, and retry states.
- Clear confirmation before cancelling an event or registration.
- Labels and explanations for unavailable actions, including full, cancelled, and started events.
- Keyboard navigation, visible focus, semantic controls, accessible labels, and sufficient contrast in both themes.
- Responsive layouts for all required pages, including organizer forms and participant lists.
- One agreed, documented university timezone for event display and validation.

These are handoff requirements; not every item has a separate high-fidelity frame. Frontend display rules do not replace backend validation, capacity consistency, authentication, or ownership checks.

## Deliverables and current limitations

Prepared design assets:

- Figma file with light, dark, and user-flow pages.
- 13 editable SVG screens per theme.
- Combined SVG boards and a separate editable user-flow chart.
- Preview images and import archives.

The Figma designs were imported from SVG and contain editable vector shapes and text. They are not yet a complete native Figma component library: reusable components, token bindings, Auto Layout refinement, and prototype navigation remain to be configured. The theme controls are visual and do not currently switch themes in a prototype. Two mobile screens demonstrate the responsive direction; the remaining mobile layouts need completion or implementation review.

Pending design work includes dedicated loading/empty/error frames, cancellation confirmations, manual completion controls, and final accessibility checks. No claim of usability testing or application acceptance testing is made by this document.

## Scope boundaries

Required workflows take priority. Profile pictures, date filtering, and organizer search are optional enhancements. The current scope excludes payments, QR attendance scanning, live streaming, personalized recommendations, complex analytics, automated email/push notifications, external calendar integration, and native mobile applications.

## Design review checklist

- [ ] Verify that all Figma pages are synced and accessible to the team.
- [ ] Review the light and dark screens against the project requirements.
- [ ] Confirm terminology, event categories, and the university timezone with the team.
- [ ] Complete pending states and prototype interactions needed for the demonstration.
- [ ] Check role visibility, ownership, and capacity-related UI behaviour with the backend developer.
- [ ] Review keyboard use, focus, contrast, and mobile layouts during implementation.
- [ ] Walk through visitor, student, and organizer flows with the frontend developer.
- [ ] Record design issues and testing results on the project board.

## Repository placement

Place this file at **`design/design.md`** in the shared repository. If the team prefers the design documentation to open automatically when viewing that folder, rename it to **`design/README.md`**. Keep the Figma link and design status updated as the project changes.
