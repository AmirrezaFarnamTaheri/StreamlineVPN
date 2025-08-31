# Test Report
==================================================

## Unit Tests

❌ **FAILED**
Return code: 2

### Output:
```
============================= test session starts =============================
platform win32 -- Python 3.10.10, pytest-8.4.1, pluggy-1.6.0
rootdir: C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-1.1.0, cov-6.2.1, mock-3.14.1
asyncio: mode=strict, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 29 items / 3 errors

=================================== ERRORS ====================================
_______________ ERROR collecting tests/test_core_components.py ________________
ImportError while importing test module 'C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-\tests\test_core_components.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python310\lib\importlib\__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_core_components.py:7: in <module>
    from vpn_merger.core.container import ServiceContainer
E   ModuleNotFoundError: No module named 'vpn_merger.core'; 'vpn_merger' is not a package
________________ ERROR collecting tests/test_ml_components.py _________________
ImportError while importing test module 'C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-\tests\test_ml_components.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python310\lib\importlib\__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_ml_components.py:10: in <module>
    from vpn_merger.ml.quality_predictor import ConfigQualityPredictor, QualityPredictor
E   ModuleNotFoundError: No module named 'vpn_merger.ml'; 'vpn_merger' is not a package
_______________ ERROR collecting tests/test_security_manager.py _______________
ImportError while importing test module 'C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-\tests\test_security_manager.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python310\lib\importlib\__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_security_manager.py:1: in <module>
    from vpn_merger.security.security_manager import SecurityManager, SecurityError
E   ModuleNotFoundError: No module named 'vpn_merger.security'; 'vpn_merger' is not a package
============================== warnings summary ===============================
..\..\..\AppData\Roaming\Python\Python310\site-packages\_pytest\config\__init__.py:1474
  C:\Users\Acer\AppData\Roaming\Python\Python310\site-packages\_pytest\config\__init__.py:1474: PytestConfigWarning: Unknown config option: env
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
ERROR tests/test_core_components.py
ERROR tests/test_ml_components.py
ERROR tests/test_security_manager.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!
======================== 1 warning, 3 errors in 1.48s =========================

```

## Integration Tests

❌ **FAILED**
Return code: 1

### Output:
```
============================= test session starts =============================
platform win32 -- Python 3.10.10, pytest-8.4.1, pluggy-1.6.0
rootdir: C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-1.1.0, cov-6.2.1, mock-3.14.1
asyncio: mode=strict, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 30 items

tests\test_e2e.py FFFFFFEE                                               [ 26%]
tests\test_performance.py FFFFFFFF                                       [ 53%]
tests\test_security.py FFFF.FF.FF....                                    [100%]

=================================== ERRORS ====================================
_ ERROR at setup of TestIntegrationComponents.test_source_to_output_integration _
file C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-\tests\test_e2e.py, line 213
      @pytest.mark.asyncio
      async def test_source_to_output_integration(self, temp_output_dir):
          """Test integration from source loading to output generation."""
          if not UnifiedSources:
              pytest.skip("UnifiedSources not available")

          merger = UnifiedSources()

          # Test the complete flow
          results = await merger.run_comprehensive_merge(
              output_dir=str(temp_output_dir),
              test_sources=True,
              max_sources=10
          )

          # Verify the integration worked
          assert results is not None
          assert len(results) > 0

          # Check that outputs are consistent
          raw_file = temp_output_dir / "vpn_subscription_raw.txt"
          base64_file = temp_output_dir / "vpn_subscription_base64.txt"

          if raw_file.exists() and base64_file.exists():
              raw_content = raw_file.read_text(encoding='utf-8')
              base64_content = base64_file.read_text(encoding='utf-8')

              # Both should have content
              assert len(raw_content) > 0
              assert len(base64_content) > 0
E       fixture 'temp_output_dir' not found
>       available fixtures: _class_scoped_runner, _function_scoped_runner, _module_scoped_runner, _package_scoped_runner, _session_scoped_runner, anyio_backend, anyio_backend_name, anyio_backend_options, cache, capfd, capfdbinary, caplog, capsys, capsysbinary, capteesys, class_mocker, cov, doctest_namespace, event_loop_policy, mocker, module_mocker, monkeypatch, no_cover, package_mocker, pytestconfig, record_property, record_testsuite_property, record_xml_attribute, recwarn, session_mocker, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory, unused_tcp_port, unused_tcp_port_factory, unused_udp_port, unused_udp_port_factory
>       use 'pytest --fixtures [testpath]' for help on them.

C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-\tests\test_e2e.py:213
_ ERROR at setup of TestIntegrationComponents.test_configuration_consistency __
file C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-\tests\test_e2e.py, line 244
      @pytest.mark.asyncio
      async def test_configuration_consistency(self, temp_output_dir):
          """Test that configurations are consistent across formats."""
          if not UnifiedSources:
              pytest.skip("UnifiedSources not available")

          merger = UnifiedSources()

          results = await merger.run_comprehensive_merge(
              output_dir=str(temp_output_dir),
              test_sources=True,
              max_sources=5
          )

          # Check consistency between raw and processed results
          raw_file = temp_output_dir / "vpn_subscription_raw.txt"
          if raw_file.exists():
              raw_content = raw_file.read_text(encoding='utf-8')
              raw_configs = [line.strip() for line in raw_content.split('\n') if line.strip()]

              # Should have similar number of configs
              assert len(raw_configs) > 0
              assert abs(len(raw_configs) - len(results)) <= 2  # Allow small difference
E       fixture 'temp_output_dir' not found
>       available fixtures: _class_scoped_runner, _function_scoped_runner, _module_scoped_runner, _package_scoped_runner, _session_scoped_runner, anyio_backend, anyio_backend_name, anyio_backend_options, cache, capfd, capfdbinary, caplog, capsys, capsysbinary, capteesys, class_mocker, cov, doctest_namespace, event_loop_policy, mocker, module_mocker, monkeypatch, no_cover, package_mocker, pytestconfig, record_property, record_testsuite_property, record_xml_attribute, recwarn, session_mocker, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory, unused_tcp_port, unused_tcp_port_factory, unused_udp_port, unused_udp_port_factory
>       use 'pytest --fixtures [testpath]' for help on them.

C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-\tests\test_e2e.py:244
================================== FAILURES ===================================
______________ TestEndToEndPipeline.test_complete_merge_pipeline ______________
tests\test_e2e.py:40: in test_complete_merge_pipeline
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
___________ TestEndToEndPipeline.test_source_loading_and_validation ___________
tests\test_e2e.py:74: in test_source_loading_and_validation
    sources = merger._try_load_external()
E   AttributeError: 'UnifiedSources' object has no attribute '_try_load_external'
_____________ TestEndToEndPipeline.test_configuration_processing ______________
tests\test_e2e.py:98: in test_configuration_processing
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
__________________ TestEndToEndPipeline.test_output_formats ___________________
tests\test_e2e.py:125: in test_output_formats
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
____________ TestEndToEndPipeline.test_error_handling_and_recovery ____________
tests\test_e2e.py:172: in test_error_handling_and_recovery
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'

During handling of the above exception, another exception occurred:
tests\test_e2e.py:181: in test_error_handling_and_recovery
    assert "Invalid" in str(e) or "Error" in str(e)
E   assert ('Invalid' in "'UnifiedSources' object has no attribute 'run_comprehensive_merge'" or 'Error' in "'UnifiedSources' object has no attribute 'run_comprehensive_merge'")
E    +  where "'UnifiedSources' object has no attribute 'run_comprehensive_merge'" = str(AttributeError("'UnifiedSources' object has no attribute 'run_comprehensive_merge'"))
E    +  and   "'UnifiedSources' object has no attribute 'run_comprehensive_merge'" = str(AttributeError("'UnifiedSources' object has no attribute 'run_comprehensive_merge'"))
______________ TestEndToEndPipeline.test_performance_under_load _______________
tests\test_e2e.py:195: in test_performance_under_load
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
________________ TestPerformanceMetrics.test_processing_speed _________________
tests\test_performance.py:49: in test_processing_speed
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
__________________ TestPerformanceMetrics.test_memory_usage ___________________
tests\test_performance.py:83: in test_memory_usage
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
______________ TestPerformanceMetrics.test_concurrent_processing ______________
tests\test_performance.py:116: in test_concurrent_processing
    task = merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
_____________ TestPerformanceMetrics.test_large_dataset_handling ______________
tests\test_performance.py:149: in test_large_dataset_handling
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
_________________ TestScalability.test_source_limit_handling __________________
tests\test_performance.py:202: in test_source_limit_handling
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
_______________ TestScalability.test_error_recovery_performance _______________
tests\test_performance.py:225: in test_error_recovery_performance
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
___________________ TestResourceOptimization.test_cpu_usage ___________________
tests\test_performance.py:266: in test_cpu_usage
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
______________ TestResourceOptimization.test_disk_io_efficiency _______________
tests\test_performance.py:296: in test_disk_io_efficiency
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
______________ TestInputValidation.test_malicious_url_detection _______________
tests\test_security.py:47: in test_malicious_url_detection
    assert not url.startswith(('javascript:', 'data:', 'file:', 'ftp:'))
E   assert not True
E    +  where True = <built-in method startswith of str object at 0x000001EFA53CF050>(('javascript:', 'data:', 'file:', 'ftp:'))
E    +    where <built-in method startswith of str object at 0x000001EFA53CF050> = "javascript:alert('xss')".startswith
______________ TestInputValidation.test_sql_injection_prevention ______________
tests\test_security.py:68: in test_sql_injection_prevention
    assert not re.search(r"('|(\\')|(;)|(--)|(union)|(select)|(drop)|(insert)|(delete))",
E   assert not <re.Match object; span=(0, 1), match="'">
E    +  where <re.Match object; span=(0, 1), match="'"> = <function search at 0x000001EFA1F1D120>("('|(\\\\')|(;)|(--)|(union)|(select)|(drop)|(insert)|(delete))", "'; drop table users; --")
E    +    where <function search at 0x000001EFA1F1D120> = re.search
E    +    and   "'; drop table users; --" = <built-in method lower of str object at 0x000001EFA53CF000>()
E    +      where <built-in method lower of str object at 0x000001EFA53CF000> = "'; DROP TABLE users; --".lower
___________________ TestInputValidation.test_xss_prevention ___________________
tests\test_security.py:84: in test_xss_prevention
    assert not re.search(r"<script|javascript:|onerror=|onload=|<iframe",
E   assert not <re.Match object; span=(0, 7), match='<script'>
E    +  where <re.Match object; span=(0, 7), match='<script'> = <function search at 0x000001EFA1F1D120>('<script|javascript:|onerror=|onload=|<iframe', "<script>alert('xss')</script>")
E    +    where <function search at 0x000001EFA1F1D120> = re.search
E    +    and   "<script>alert('xss')</script>" = <built-in method lower of str object at 0x000001EFA5CC1A70>()
E    +      where <built-in method lower of str object at 0x000001EFA5CC1A70> = "<script>alert('xss')</script>".lower
_____________ TestInputValidation.test_path_traversal_prevention ______________
tests\test_security.py:106: in test_path_traversal_prevention
    assert not '..' in malicious_path
E   AssertionError: assert not '..' in '../../../etc/passwd'
_____________ TestThreatDetection.test_malicious_config_detection _____________
tests\test_security.py:153: in test_malicious_config_detection
    assert not 'evil.com' in config.lower()
E   AssertionError: assert not 'evil.com' in 'trojan://malicious@evil.com:443?security=tls&type=tcp&headertype=none#malicious'
E    +  where 'trojan://malicious@evil.com:443?security=tls&type=tcp&headertype=none#malicious' = <built-in method lower of str object at 0x000001EFA5CC6430>()
E    +    where <built-in method lower of str object at 0x000001EFA5CC6430> = 'trojan://malicious@evil.com:443?security=tls&type=tcp&headerType=none#Malicious'.lower
___________________ TestThreatDetection.test_rate_limiting ____________________
tests\test_security.py:165: in test_rate_limiting
    start_time = time.time()
E   NameError: name 'time' is not defined
___________________ TestDataProtection.test_data_encryption ___________________
tests\test_security.py:230: in test_data_encryption
    results = await merger.run_comprehensive_merge(
E   AttributeError: 'UnifiedSources' object has no attribute 'run_comprehensive_merge'
__________________ TestDataProtection.test_log_sanitization ___________________
tests\test_security.py:257: in test_log_sanitization
    assert "***REDACTED***" in sanitized
E   AssertionError: assert '***REDACTED***' in 'API key=sk-1234567890abcdef used'
============================== warnings summary ===============================
..\..\..\AppData\Roaming\Python\Python310\site-packages\_pytest\config\__init__.py:1474
  C:\Users\Acer\AppData\Roaming\Python\Python310\site-packages\_pytest\config\__init__.py:1474: PytestConfigWarning: Unknown config option: env
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.10.10-final-0 _______________

Name            Stmts   Miss  Cover
-----------------------------------
vpn_merger.py     418    298    29%
-----------------------------------
TOTAL             418    298    29%
Coverage HTML written to dir htmlcov
Coverage JSON written to file coverage.json
=========================== short test summary info ===========================
FAILED tests/test_e2e.py::TestEndToEndPipeline::test_complete_merge_pipeline
FAILED tests/test_e2e.py::TestEndToEndPipeline::test_source_loading_and_validation
FAILED tests/test_e2e.py::TestEndToEndPipeline::test_configuration_processing
FAILED tests/test_e2e.py::TestEndToEndPipeline::test_output_formats - Attribu...
FAILED tests/test_e2e.py::TestEndToEndPipeline::test_error_handling_and_recovery
FAILED tests/test_e2e.py::TestEndToEndPipeline::test_performance_under_load
FAILED tests/test_performance.py::TestPerformanceMetrics::test_processing_speed
FAILED tests/test_performance.py::TestPerformanceMetrics::test_memory_usage
FAILED tests/test_performance.py::TestPerformanceMetrics::test_concurrent_processing
FAILED tests/test_performance.py::TestPerformanceMetrics::test_large_dataset_handling
FAILED tests/test_performance.py::TestScalability::test_source_limit_handling
FAILED tests/test_performance.py::TestScalability::test_error_recovery_performance
FAILED tests/test_performance.py::TestResourceOptimization::test_cpu_usage - ...
FAILED tests/test_performance.py::TestResourceOptimization::test_disk_io_efficiency
FAILED tests/test_security.py::TestInputValidation::test_malicious_url_detection
FAILED tests/test_security.py::TestInputValidation::test_sql_injection_prevention
FAILED tests/test_security.py::TestInputValidation::test_xss_prevention - ass...
FAILED tests/test_security.py::TestInputValidation::test_path_traversal_prevention
FAILED tests/test_security.py::TestThreatDetection::test_malicious_config_detection
FAILED tests/test_security.py::TestThreatDetection::test_rate_limiting - Name...
FAILED tests/test_security.py::TestDataProtection::test_data_encryption - Att...
FAILED tests/test_security.py::TestDataProtection::test_log_sanitization - As...
ERROR tests/test_e2e.py::TestIntegrationComponents::test_source_to_output_integration
ERROR tests/test_e2e.py::TestIntegrationComponents::test_configuration_consistency
============= 22 failed, 6 passed, 1 warning, 2 errors in 12.62s ==============

```

## All Tests

❌ **FAILED**
Return code: 2

### Output:
```
============================= test session starts =============================
platform win32 -- Python 3.10.10, pytest-8.4.1, pluggy-1.6.0
rootdir: C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-1.1.0, cov-6.2.1, mock-3.14.1
asyncio: mode=strict, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 59 items / 3 errors

=================================== ERRORS ====================================
_______________ ERROR collecting tests/test_core_components.py ________________
ImportError while importing test module 'C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-\tests\test_core_components.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python310\lib\importlib\__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_core_components.py:7: in <module>
    from vpn_merger.core.container import ServiceContainer
E   ModuleNotFoundError: No module named 'vpn_merger.core'; 'vpn_merger' is not a package
________________ ERROR collecting tests/test_ml_components.py _________________
ImportError while importing test module 'C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-\tests\test_ml_components.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python310\lib\importlib\__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_ml_components.py:10: in <module>
    from vpn_merger.ml.quality_predictor import ConfigQualityPredictor, QualityPredictor
E   ModuleNotFoundError: No module named 'vpn_merger.ml'; 'vpn_merger' is not a package
_______________ ERROR collecting tests/test_security_manager.py _______________
ImportError while importing test module 'C:\Users\Acer\Documents\GitHub\CleanConfigs-SubMerger-\tests\test_security_manager.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python310\lib\importlib\__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_security_manager.py:1: in <module>
    from vpn_merger.security.security_manager import SecurityManager, SecurityError
E   ModuleNotFoundError: No module named 'vpn_merger.security'; 'vpn_merger' is not a package
============================== warnings summary ===============================
..\..\..\AppData\Roaming\Python\Python310\site-packages\_pytest\config\__init__.py:1474
  C:\Users\Acer\AppData\Roaming\Python\Python310\site-packages\_pytest\config\__init__.py:1474: PytestConfigWarning: Unknown config option: env
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
ERROR tests/test_core_components.py
ERROR tests/test_ml_components.py
ERROR tests/test_security_manager.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!
======================== 1 warning, 3 errors in 0.67s =========================

```
