# GIDS Mobile Evacuation — Local Integration Test Checklist

## Environment

- [ ] Railway backend is online
- [ ] Railway PostgreSQL is online
- [ ] Railway backend `/api/health` returns `status: ok`
- [ ] Railway backend `/api/mobile/health` returns `status: ok`
- [ ] Mobile app uses Railway backend URL through `GIDS_API_BASE_URL`
- [ ] Android emulator or physical Android device has internet access
- [ ] Android GPS/location services are enabled
- [ ] Flutter analyze returns `No issues found!`

## Backend and database tests

- [ ] Device registration succeeds
- [ ] Re-registering same device UUID succeeds without duplicate rows
- [ ] Fresh location upload succeeds
- [ ] `accuracy_m <= 100` returns `accuracy_status: OK`
- [ ] `accuracy_m > 100` returns `accuracy_status: LOW_ACCURACY`
- [ ] Assignment returns a valid business status
- [ ] Nearest shelters endpoint returns a list
- [ ] Assignment acknowledgment succeeds
- [ ] Notification unread count endpoint succeeds
- [ ] Notification list endpoint succeeds
- [ ] Mark notification read succeeds
- [ ] Mark all notifications read succeeds

## Mobile UI tests

- [ ] Splash screen opens
- [ ] Welcome/onboarding opens on first launch
- [ ] Skip button works
- [ ] Get Started button works
- [ ] Location permission request appears
- [ ] Allowing location permission opens Assignment screen
- [ ] Denying location permission shows a clear message
- [ ] Assignment screen displays correct status
- [ ] Pull-to-refresh refreshes location and assignment
- [ ] Nearby shelters screen loads
- [ ] Shelter detail screen opens
- [ ] Maps navigation action opens a maps application/browser
- [ ] Notification bell appears
- [ ] Notification unread badge updates
- [ ] Notifications inbox opens
- [ ] Opening an unread notification marks it as read
- [ ] Scenario update notification opens Assignment screen
- [ ] Location reminder notification opens Location Permission screen

## Safety checks

- [ ] Mobile assignment does not change Module 4 `AssignedPopulation`
- [ ] Mobile assignment does not change Module 4 `RemainingCapacity`
- [ ] Mobile assignment does not reserve beds
- [ ] Existing web dashboard remains functional
- [ ] Existing scenario creation remains functional
- [ ] Existing scenario re-run remains functional
- [ ] No API key, DATABASE_URL, Firebase private key, or password is in source code

## APK readiness

- [ ] `flutter analyze` has no issues
- [ ] App launches on a physical Android device
- [ ] Location permission works on a physical Android device
- [ ] Railway API calls work on mobile data/Wi-Fi
- [ ] Assignment flow works end-to-end
- [ ] Notification inbox works