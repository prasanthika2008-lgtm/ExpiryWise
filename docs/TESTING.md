# ExpiryWise – Testing Documentation

## 1. Overview

ExpiryWise uses automated testing to verify the functionality, reliability and stability of the application.

The testing process covers product management, input validation, expiry date calculations, barcode lookup, OCR processing, recommendations, recipes, dashboard statistics and error handling.

The application uses pytest for automated testing and GitHub Actions for Continuous Integration.

## 2. Testing Tools

| Tool | Purpose |
|---|---|
| pytest | Automated testing |
| pytest-cov | Code coverage measurement |
| Flask Test Client | Application route testing |
| Python | Test execution |
| GitHub Actions | Continuous Integration |

## 3. How to Run Tests

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest -v
```

### Display Skipped Test Reasons

```bash
pytest -v -rs
```

### Generate Coverage Report

```bash
pytest --cov=. --cov-report=term-missing
```

## 4. Testing Strategy

The following application components are covered by the testing strategy.

| Module | Testing Approach |
|---|---|
| Product Management | Product creation, editing and deletion |
| Input Validation | Empty, invalid and incorrect inputs |
| Expiry Tracking | Remaining days and expiry status |
| Barcode Lookup | Valid and invalid barcode handling |
| OCR | Expiry date parsing and extraction |
| Recommendations | Product-based recommendations |
| Recipes | Recipe response validation |
| Dashboard | Statistics and category counts |
| Error Handling | HTTP error responses |
| Database | Data storage and retrieval |

## 5. Test Files

| Test File | Description |
|---|---|
| tests/test_expirywise.py | Core application functionality |
| tests/test_error_handling.py | Application error handling |

## 6. Error Handling Test Cases

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| EH01 | Unknown URL | 404 Not Found |
| EH02 | Invalid request | 400 Bad Request |
| EH03 | Incorrect HTTP method | 405 Method Not Allowed |
| EH04 | File exceeds upload limit | 413 File Too Large |
| EH05 | Unexpected server exception | 500 Internal Server Error |
| EH06 | Unknown route in application | 404 response |
| EH07 | GET request to delete endpoint | 405 response |
| EH08 | Invalid barcode | 400 response |
| EH09 | OCR request without image | 400 response |

## 7. Error Handling Design

ExpiryWise uses centralized error handlers and input validation to prevent application failures.

| Component | Possible Error | Handling |
|---|---|---|
| Product Validation | Empty product name | Validation message |
| Product Validation | Invalid expiry date | Validation message |
| Product Validation | Invalid quantity | Validation message |
| Barcode | Invalid barcode | Error response |
| Barcode API | Network failure | Service unavailable response |
| OCR | Missing image | Bad request response |
| OCR | Tesseract unavailable | Service unavailable response |
| OCR | Invalid image | Error response |
| Database | Invalid database values | Safe error handling |
| Routes | Unknown URL | 404 handler |
| Routes | Incorrect HTTP method | 405 handler |
| Upload | File exceeds size limit | 413 handler |
| Application | Unexpected exception | 500 handler |

## 8. Test Execution Results

The test execution results must be recorded using the actual output from pytest.

Command:

```bash
pytest -v -rs
```

Record the following:

- Total number of tests:
- Passed tests:
- Failed tests:
- Skipped tests:

Results should be updated after the latest test execution.

## 9. Skipped Tests

Skipped tests must be reviewed individually.

The following information should be recorded when a test is skipped:

- Test name.
- Reason for skipping.
- Required dependency or environment condition.
- Whether the test can be executed after resolving the condition.

Optional dependencies such as Tesseract OCR may require additional installation and configuration.

## 10. Continuous Integration

ExpiryWise uses GitHub Actions to automate testing.

Workflow file:

```text
.github/workflows/tests.yml
```

The workflow performs the following operations:

1. Checks out the GitHub repository.
2. Sets up the Python environment.
3. Installs project dependencies.
4. Runs the automated test suite.
5. Reports the workflow result.

A successful workflow indicates that the configured automated tests completed successfully.

## 11. Manual Testing

The following features should also be verified manually.

| Test ID | Feature | Expected Result |
|---|---|---|
| MT01 | Add Product | Product is added |
| MT02 | Edit Product | Product details are updated |
| MT03 | Delete Product | Product is removed |
| MT04 | Search Product | Matching product is displayed |
| MT05 | Filter Product | Correct products are displayed |
| MT06 | Expiry Tracking | Correct expiry status is displayed |
| MT07 | Barcode Scanner | Product details are retrieved |
| MT08 | OCR Scanner | Expiry date is extracted |
| MT09 | Dashboard | Correct statistics are displayed |
| MT10 | Recipe Suggestions | Relevant suggestions are displayed |

## 12. Performance and Reliability

The application should be checked for:

- Correct product data storage.
- Reliable expiry date calculations.
- Proper input validation.
- Appropriate error messages.
- Safe handling of invalid requests.
- Stable application behaviour when external APIs are unavailable.

## 13. Conclusion

Testing helps ensure that ExpiryWise functions correctly and reliably.

Automated testing, manual verification, input validation and centralized error handling help improve the application's stability and maintainability.

Continuous Integration provides an additional verification step whenever changes are pushed to the GitHub repository.