Changelog
=========

3.0.0
-----

Changes:

- [feature] Support class-based check
- [feature] Support nested spec class
- [feature] Support combining request query parameters with payload for POST/PUT/DELETE Request
- Checker keyword "extra" is removed.


2.1.1
-----

Changes:

- [fix] Export `FLOAT`, `DATE_OBJECT`, `DATETIME_OBJECT` check str


2.1.0
-----

Changes:

- [feature] add `FLOAT`, `DATE_OBJECT`, `DATETIME_OBJECT` check to validate python built-in type. Derived instances are
  not considered valid and you can use custom spec in these cases.
- Update README


2.0.0
-----

Changes:

- [feature] add `multirow` option in `@dsv` and `def validate_data_spec` to validate list of SPEC naturally.
- Update README


1.9.0
-----

Changes:

- [feature] new dsv_feature `err_mode` to collect all validation errors into exception arguments.
- [improvement] Spec name is now added before the field name in error message.
- Check `KEY_COEXISTS`, `ANY_KEY_EXISTS` are deprecated.
- Update README


1.8.0
-----

Changes:

- [fix] COND_EXIST now works with other checks correctly.
- [feature] Add new check `FOREACH`, used for any iterable.
- [behavior-change] `LIST_OF` enforce LIST type validation as well
- [behavior-change] Use `warning.warn` instead of `print`
- [internal] More type hint
- Postpone {KEY_COEXISTS, ANY_KEY_EXISTS} deprecation, will remove them in 1.9.0
- Update README


1.7.0
-----

Changes:

- Add new check COND_EXIST to support conditional key existence. More sample usage in test.
- Add deprecating messages for Check: KEY_COEXISTS, ANY_KEY_EXISTS
- Add test cases.
- DEPRECATIONS: KEY_COEXISTS, ANY_KEY_EXISTS will be removed in 1.8.0


1.6.0
-----

Changes:

- Support checks as keyword argument when building checker.
- Add test cases.


1.5.0
-----

Changes:

- Add type hints
- Support strict mode to detect unexpected key/value parameters


1.4.0
-----

Changes:

- Improve error message readability
- Provide `reset_msg_level` function to change the displayed messages
- Add `allow_none` option for `Checker` to support `None` value

1.3.1
-----

Changes:

- Change email validator regular expression (https://html.spec.whatwg.org/multipage/input.html#valid-e-mail-address)

1.3.0
-----

Changes:

- Fix package version
- String type UUID now can pass UUIDValidator

...
