# MedScanner Test Suite

This directory contains comprehensive unit tests for the MedScanner application. The test suite covers all major components including models, routes, and utility functions.

## Test Structure

### Test Files

- **`test_models.py`** - Tests for database models (User, Medication, DrugInteraction, Prescription, etc.)
- **`test_routes.py`** - Tests for web application routes and endpoints
- **`test_utils.py`** - Tests for utility functions (OCR, drug interactions, dosage verification, inventory)
- **`conftest.py`** - Test configuration and shared fixtures

### Test Categories

#### Model Tests (`TestUser`, `TestMedication`, `TestDrugInteraction`, etc.)
- User creation and authentication
- Password hashing and verification
- Role assignments and permissions
- Medication management
- Drug interaction relationships
- Prescription handling

#### Route Tests
- **Public Routes** - Pages accessible without login (index, scan, public interactions)
- **Authentication Routes** - Login, registration, logout functionality
- **Protected Routes** - Dashboard, profile, reports (require authentication)
- **API Endpoints** - Medication search, scan processing
- **Error Handling** - 404 errors, invalid requests
- **Session Management** - User sessions, temporary data storage

#### Utility Tests
- **Dosage Verification** - Age-appropriate dosing, weight-based calculations
- **Drug Interaction Detection** - Known interactions, severity assessment
- **Inventory Management** - Stock updates, low stock alerts
- **OCR Processing** - Text extraction, medication parsing (with mocked AI services)

## Running Tests

### Prerequisites

Ensure you have the required testing packages installed:
```bash
pip install pytest pytest-flask pytest-cov
```

### Basic Test Execution

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_models.py

# Run specific test class
python -m pytest tests/test_models.py::TestUser

# Run specific test
python -m pytest tests/test_models.py::TestUser::test_user_creation
```

### Using the Test Runner Script

```bash
# Run all tests with verbose output
python run_tests.py --type all --verbose

# Run only model tests
python run_tests.py --type models

# Run only route tests
python run_tests.py --type routes

# Run only utility tests
python run_tests.py --type utils

# Run with coverage report
python run_tests.py --coverage
```

## Test Configuration

### Database Setup
Tests use SQLite in-memory database for isolation and speed. Each test gets a fresh database instance with:
- Clean schema creation
- Sample test data (users, medications, interactions)
- Proper teardown after each test

### Fixtures

#### `test_app`
Provides a Flask test client with:
- SQLite test database
- Disabled CSRF protection
- Test-specific configuration

#### `test_db`
Creates test database with sample data:
- Three user roles (patient, doctor, pharmacist)
- Test users for each role
- Sample medications (Ibuprofen, Acetaminophen, Warfarin, Aspirin)
- Known drug interactions

#### `sample_prescription_data`
Provides mock prescription data for testing scan functionality

### Mocking External Services

Tests mock external dependencies:
- **OpenAI API** - For OCR and AI-powered medication extraction
- **Image Processing** - OpenCV operations for prescription scanning
- **Database Operations** - Use test database instead of production

## Test Coverage

The test suite covers:

### Authentication & Authorization
- User registration and login
- Password security
- Role-based access control
- Session management

### Core Functionality
- Prescription scanning and processing
- Drug interaction detection
- Dosage verification
- Inventory tracking

### User Interface
- Public pages (accessible without login)
- Protected pages (require authentication)
- Error handling and validation
- Multi-language support

### Data Integrity
- Model relationships and constraints
- Database operations and transactions
- Input validation and sanitization

## Best Practices

### Writing New Tests

1. **Use descriptive test names** that explain what is being tested
2. **Follow the AAA pattern** - Arrange, Act, Assert
3. **Test one thing per test** - Keep tests focused and atomic
4. **Use fixtures** for common setup and test data
5. **Mock external dependencies** to ensure tests are reliable and fast

### Test Data Management

- Use the provided fixtures for consistent test data
- Create minimal test data needed for each test
- Clean up after tests automatically through fixtures
- Don't rely on data from other tests

### Mocking Guidelines

- Mock external APIs and services
- Use realistic mock responses that match actual service behavior
- Test both success and failure scenarios
- Document what is being mocked and why

## Troubleshooting

### Common Issues

**Database Connection Errors**
- Tests use SQLite, so no PostgreSQL connection needed
- Each test gets a fresh database instance

**Import Errors**
- Ensure all dependencies are installed
- Check that the application modules can be imported

**Slow Tests**
- Some tests involve database operations and may take time
- Use `--tb=short` for quicker feedback on failures

### Environment Variables

Tests handle missing environment variables gracefully:
- `OPENAI_API_KEY` - Mocked for OCR tests
- `DATABASE_URL` - Overridden to use SQLite for tests

## Contributing

When adding new features:

1. Write tests for new functionality
2. Ensure existing tests still pass
3. Add integration tests for user-facing features
4. Update this documentation if needed

The test suite is designed to catch regressions and ensure the application works correctly across different scenarios and user types.