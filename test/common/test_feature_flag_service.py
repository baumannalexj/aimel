from __future__ import annotations

import unittest

from common.feature_flag_service import (
    EmailRespondFlag,
    FeatureFlagService,
    FlagState,
    IFeatureFlag,
)


class StubFlag(IFeatureFlag):
    def __init__(self, key: str, state: FlagState):
        self._key = key
        self._state = state

    @property
    def key(self) -> str:
        return self._key

    @property
    def state(self) -> FlagState:
        return self._state


class FeatureFlagServiceTest(unittest.TestCase):
    def test_email_respond_is_on_by_default(self) -> None:
        service = FeatureFlagService.with_defaults()

        self.assertTrue(service.is_enabled(EmailRespondFlag.KEY))

    def test_a_disabled_flag_gates(self) -> None:
        service = FeatureFlagService({EmailRespondFlag.KEY: EmailRespondFlag(FlagState.DISABLED)})

        self.assertFalse(service.is_enabled(EmailRespondFlag.KEY))

    def test_an_unknown_key_is_a_mistake_not_a_silent_false(self) -> None:
        service = FeatureFlagService.with_defaults()

        with self.assertRaises(KeyError):
            service.is_enabled("no_such_flag")

    def test_flags_are_addressed_by_their_own_key(self) -> None:
        service = FeatureFlagService({"a": StubFlag("a", FlagState.ENABLED),
                                      "b": StubFlag("b", FlagState.DISABLED)})

        self.assertTrue(service.is_enabled("a"))
        self.assertFalse(service.is_enabled("b"))

    def test_environment_can_disable_a_flag_without_a_code_change(self) -> None:
        service = FeatureFlagService.with_defaults(environ={"AIMEL_FLAG_EMAIL_RESPOND": "disabled"})

        self.assertFalse(service.is_enabled(EmailRespondFlag.KEY))




class ImmutabilityTest(unittest.TestCase):
    """The server is threaded, so read-only-after-construction is the whole safety argument."""

    def test_the_flag_mapping_cannot_be_mutated_after_construction(self) -> None:
        service = FeatureFlagService.with_defaults(environ={})

        with self.assertRaises(TypeError):
            service._flags["email_respond"] = EmailRespondFlag(FlagState.DISABLED)

    def test_a_flag_cannot_be_flipped_in_place(self) -> None:
        flag = EmailRespondFlag(FlagState.ENABLED)

        with self.assertRaises(Exception):
            flag.flag_state = FlagState.DISABLED

    def test_constructing_from_a_dict_copies_it_so_the_caller_cannot_reach_in(self) -> None:
        source = {EmailRespondFlag.KEY: EmailRespondFlag(FlagState.ENABLED)}
        service = FeatureFlagService(source)

        source[EmailRespondFlag.KEY] = EmailRespondFlag(FlagState.DISABLED)

        self.assertTrue(service.is_enabled(EmailRespondFlag.KEY))

if __name__ == "__main__":
    unittest.main()
