import unittest

from orville_core.extensions import Connector, ExtensionRegistry, Hook, HookDispatcher, PermissionSet, Plugin, Skill, Subagent


class ExtensionTests(unittest.TestCase):
    def test_permissions_are_checked_for_skills_and_plugins(self):
        registry = ExtensionRegistry()
        grant = PermissionSet(tools=frozenset({"read_file"}))
        registry.install_skill(Skill("safe", "1.0.0", "read only", required_tools=("read_file",), permissions=PermissionSet(tools=frozenset({"read_file"}))), granted=grant)
        with self.assertRaises(PermissionError):
            registry.install_skill(Skill("unsafe", "1.0.0", "write", permissions=PermissionSet(tools=frozenset({"write_file"}))), granted=grant)
        with self.assertRaises(PermissionError):
            registry.install_plugin(Plugin("plugin", "1.0.0", verified=False), granted=grant, administrator_approved=True)
        registry.install_plugin(Plugin("plugin", "1.0.0", verified=True), granted=grant, administrator_approved=True)

    def test_hook_dispatch_requires_task_permissions(self):
        registry = ExtensionRegistry()
        registry.register_connector(Connector("local", "local", enabled=True))
        registry.register_hook(Hook("hook", "task-created", "record", PermissionSet(tools=frozenset({"record"})), enabled=True), granted=PermissionSet(tools=frozenset({"record"})))
        dispatcher = HookDispatcher(registry, {"record": lambda payload: payload["id"]})
        self.assertEqual(dispatcher.dispatch("task-created", {"id": "task-1"}, task_permissions=PermissionSet(tools=frozenset({"record"}))), ["task-1"])
        with self.assertRaises(PermissionError):
            dispatcher.dispatch("task-created", {"id": "task-1"}, task_permissions=PermissionSet())

    def test_subagent_permissions_are_scoped(self):
        registry = ExtensionRegistry()
        agent = Subagent("tester", "testing", ("testing",), PermissionSet(tools=frozenset({"run_tests"})))
        with self.assertRaises(PermissionError):
            registry.register_subagent(agent, granted=PermissionSet())
        registry.register_subagent(agent, granted=PermissionSet(tools=frozenset({"run_tests"})))


if __name__ == "__main__":
    unittest.main()
