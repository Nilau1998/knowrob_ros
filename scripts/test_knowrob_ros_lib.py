#!/usr/bin/env python3

import subprocess
import time
import uuid

import pytest
import rclpy
from rclpy.action import ActionClient

from knowrob_ros.action import (
    AskAll,
    AskIncremental,
    AskIncrementalNextSolution,
    AskOne,
    Tell,
)
from knowrob_ros.msg import KeyValuePair, ModalFrame, Triple
from knowrob_ros.srv import AskIncrementalFinish


def _default_modal_frame():
    frame = ModalFrame()
    frame.epistemic_operator = ModalFrame.KNOWLEDGE
    frame.temporal_operator = ModalFrame.CURRENTLY
    frame.min_past_timestamp = ModalFrame.UNSPECIFIED_TIMESTAMP
    frame.max_past_timestamp = ModalFrame.UNSPECIFIED_TIMESTAMP
    frame.confidence = 0.0
    return frame


def _answer_to_dict(answer_msg):
    result = {}
    for kv in answer_msg.substitution:
        if kv.type == KeyValuePair.TYPE_STRING:
            result[kv.key] = kv.value_string
        elif kv.type == KeyValuePair.TYPE_FLOAT:
            result[kv.key] = kv.value_float
        elif kv.type == KeyValuePair.TYPE_INT:
            result[kv.key] = kv.value_int
        elif kv.type == KeyValuePair.TYPE_LONG:
            result[kv.key] = kv.value_long
        elif kv.type == KeyValuePair.TYPE_VARIABLE:
            result[kv.key] = kv.value_variable
        elif kv.type == KeyValuePair.TYPE_PREDICATE:
            result[kv.key] = kv.value_predicate
        elif kv.type == KeyValuePair.TYPE_LIST:
            result[kv.key] = kv.value_list
    return result


def _send_action_goal(node, client, goal_msg, timeout_sec=20.0):
    send_future = client.send_goal_async(goal_msg)
    rclpy.spin_until_future_complete(node, send_future, timeout_sec=timeout_sec)
    goal_handle = send_future.result()
    assert goal_handle is not None
    assert goal_handle.accepted

    result_future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future, timeout_sec=timeout_sec)
    wrapped_result = result_future.result()
    assert wrapped_result is not None
    return wrapped_result.result


@pytest.fixture(scope="module")
def ros_fixture():
    rclpy.init()
    node = rclpy.create_node("test_knowrob_ros_lib")

    process = subprocess.Popen(["ros2", "run", "knowrob_ros", "knowrob_ros_node"])
    time.sleep(1.0)

    ask_one_client = ActionClient(node, AskOne, "knowrob/askone")
    ask_all_client = ActionClient(node, AskAll, "knowrob/askall")
    ask_incremental_client = ActionClient(node, AskIncremental, "knowrob/askincremental")
    ask_incremental_next_client = ActionClient(
        node, AskIncrementalNextSolution, "knowrob/askincremental_next_solution"
    )
    tell_client = ActionClient(node, Tell, "knowrob/tell")
    finish_client = node.create_client(AskIncrementalFinish, "knowrob/askincremental_finish")

    assert ask_one_client.wait_for_server(timeout_sec=30.0)
    assert ask_all_client.wait_for_server(timeout_sec=30.0)
    assert ask_incremental_client.wait_for_server(timeout_sec=30.0)
    assert ask_incremental_next_client.wait_for_server(timeout_sec=30.0)
    assert tell_client.wait_for_server(timeout_sec=30.0)
    assert finish_client.wait_for_service(timeout_sec=30.0)

    yield {
        "node": node,
        "ask_one": ask_one_client,
        "ask_all": ask_all_client,
        "ask_incremental": ask_incremental_client,
        "ask_incremental_next": ask_incremental_next_client,
        "tell": tell_client,
        "finish": finish_client,
    }

    process.terminate()
    process.wait(timeout=10)
    node.destroy_node()
    rclpy.shutdown()


def test_knowrob_actions_and_service(ros_fixture):
    node = ros_fixture["node"]
    ask_one_client = ros_fixture["ask_one"]
    ask_all_client = ros_fixture["ask_all"]
    ask_incremental_client = ros_fixture["ask_incremental"]
    ask_incremental_next_client = ros_fixture["ask_incremental_next"]
    tell_client = ros_fixture["tell"]
    finish_client = ros_fixture["finish"]

    unique_subject = f"alice_{uuid.uuid4().hex[:8]}"
    frame = _default_modal_frame()

    tell_goal = Tell.Goal()
    triple = Triple()
    triple.subject = unique_subject
    triple.predicate = "marriedTo"
    triple.object = "frank"
    tell_goal.tell.triples = [triple]
    tell_goal.tell.frame = frame

    tell_result = _send_action_goal(node, tell_client, tell_goal)
    assert tell_result.status == Tell.Result.TRUE

    ask_one_goal = AskOne.Goal()
    ask_one_goal.query.query_string = f"marriedTo({unique_subject}, X)"
    ask_one_goal.query.frame = frame
    ask_one_goal.query.lang = "LANG_FOL"
    ask_one_result = _send_action_goal(node, ask_one_client, ask_one_goal)
    assert ask_one_result.status == AskOne.Result.TRUE
    ask_one_binding = _answer_to_dict(ask_one_result.answer)
    assert "X" in ask_one_binding
    assert "frank" in str(ask_one_binding["X"])

    ask_all_goal = AskAll.Goal()
    ask_all_goal.query.query_string = f"marriedTo({unique_subject}, X)"
    ask_all_goal.query.frame = frame
    ask_all_goal.query.lang = "LANG_FOL"
    ask_all_result = _send_action_goal(node, ask_all_client, ask_all_goal)
    assert ask_all_result.status == AskAll.Result.TRUE
    all_bindings = [_answer_to_dict(answer) for answer in ask_all_result.answers]
    assert any("frank" in str(binding.get("X", "")) for binding in all_bindings)

    start_goal = AskIncremental.Goal()
    start_goal.query.query_string = f"marriedTo({unique_subject}, X)"
    start_goal.query.frame = frame
    start_goal.query.lang = "LANG_FOL"
    start_result = _send_action_goal(node, ask_incremental_client, start_goal)
    assert start_result.status
    assert start_result.query_id > 0

    next_goal = AskIncrementalNextSolution.Goal()
    next_goal.query_id = start_result.query_id
    next_result = _send_action_goal(node, ask_incremental_next_client, next_goal)
    assert next_result.status == AskIncrementalNextSolution.Result.TRUE
    next_binding = _answer_to_dict(next_result.answer)
    assert "X" in next_binding
    assert "frank" in str(next_binding["X"])

    finish_req = AskIncrementalFinish.Request()
    finish_req.query_id = start_result.query_id
    finish_future = finish_client.call_async(finish_req)
    rclpy.spin_until_future_complete(node, finish_future, timeout_sec=10.0)
    finish_response = finish_future.result()
    assert finish_response is not None
    assert finish_response.success
