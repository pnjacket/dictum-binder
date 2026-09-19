"""Unit tier: every ERR-* class constructs with its catalog code and exit code; the Renderer's
projections of error details that carry findings or an anchor (used from slice 2 onwards)."""

from __future__ import annotations

import json
import unittest

from lspd import errors, render
from lspd.model import Anchor, Finding

FINDING = Finding("INV-PATH-FORM", "error", Anchor("locator", id="ENTITY-A", path="../x"), "msg", 7)


class ErrorCatalogConstructors(unittest.TestCase):
    """DICT: ERR-SCHEMA-VERSION / ERR-FILE-INVALID / ERR-NOT-FOUND / ERR-DUPLICATE.

    Also ERR-INPUT-INVALID.
    """

    def test_each_error_carries_code_exit_and_details(self) -> None:
        anchor = Anchor("binding", id="ENTITY-A")
        cases: list[tuple[errors.LspdError, str, int, dict[str, object]]] = [
            (
                errors.SchemaVersionError(2, 1),
                "ERR-SCHEMA-VERSION",
                1,
                {"found": 2, "expected": 1},
            ),
            (errors.FileInvalidError([FINDING]), "ERR-FILE-INVALID", 1, {"findings": [FINDING]}),
            (
                errors.NotFoundError("no such binding", "ENTITY-A", anchor),
                "ERR-NOT-FOUND",
                1,
                {"id": "ENTITY-A", "anchor": anchor},
            ),
            (
                errors.DuplicateError("already present", "ENTITY-A", anchor),
                "ERR-DUPLICATE",
                1,
                {"id": "ENTITY-A", "anchor": anchor},
            ),
            (
                errors.InputInvalidError([FINDING]),
                "ERR-INPUT-INVALID",
                1,
                {"findings": [FINDING]},
            ),
        ]
        for err, code, exit_code, details in cases:
            with self.subTest(code=code):
                self.assertEqual((err.code, err.exit_code, err.details), (code, exit_code, details))
                self.assertTrue(str(err))


class RendererProjections(unittest.TestCase):
    """DICT: OUT-ERROR — findings and anchors inside error details are projected, not repr'd."""

    def test_findings_and_anchor_details(self) -> None:
        projected = render.error(errors.FileInvalidError([FINDING]))
        self.assertEqual(projected["details"]["findings"], [render.finding(FINDING)])
        anchor = Anchor("binding", id="ENTITY-A")
        projected = render.error(errors.NotFoundError("no such binding", "ENTITY-A", anchor))
        self.assertEqual(projected["details"]["anchor"], render.anchor(anchor))

    def test_human_rendering_lists_the_findings_of_an_error(self) -> None:
        err = errors.InputInvalidError([FINDING])
        text = render.render("set", None, [], [], err, version="0", schema_version=1, human=True)
        self.assertIn("  findings:", text)
        self.assertIn("INV-PATH-FORM", text)
        envelope = render.render(
            "set", None, [], [], err, version="0", schema_version=1, human=False
        )
        self.assertEqual(json.loads(envelope)["error"]["code"], "ERR-INPUT-INVALID")


if __name__ == "__main__":  # pragma: no cover — direct invocation convenience
    unittest.main()
