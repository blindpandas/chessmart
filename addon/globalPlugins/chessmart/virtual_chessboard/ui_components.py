# coding: utf-8

# Copyright (c) 2021 Blind Pandas Team
# This file is covered by the GNU General Public License.

import tones
import api
import ui
import controlTypes
import speech
import queueHandler
import eventHandler
from contextlib import suppress
from NVDAObjects import NVDAObject
from scriptHandler import script
from ..helpers import GameSound


class KeyboardNavigableNVDAObjectMixin:
    windowClassName = ""
    windowControlID = 0
    windowThreadID = -1
    windowHandle = -1

    # This should be set to Tru in the final release
    # It prevent any key strokes from reaching the application
    CAPTURE_KEYS_WHILE_IN_FOCUS = False

    def script_do_nothing(self, gesture):
        pass

    def getScript(self, gesture):
        """Ensures that no keys are sent to the underlying text control."""
        script = NVDAObject.getScript(self, gesture)
        if self.CAPTURE_KEYS_WHILE_IN_FOCUS and script is None:
            return self.script_do_nothing
        return script


class ItemContainerMixin:
    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def index_of(self, item):
        items_hashes = [hash(i) for i in self.items]
        item_hash = hash(item)
        if item_hash in items_hashes:
            return items_hashes.index(item_hash)

    def init_container_state(self, items, on_top_edge=None, on_bottom_edge=None):
        self.items = items
        self.children = items
        self.controllerFor = self.children
        self.on_top_edge = on_top_edge
        self.on_bottom_edge = on_bottom_edge
        self._current_index = 0

    def set_current(self, index):
        if index not in range(len(self)):
            raise ValueError("Index out of range")
        self._current_index = index

    def get_item(self, index):
        with suppress(IndexError):
            return self.items[index]

    def get_current_item(self):
        return self.get_item(self._current_index)

    def remove_item(self, item):
        item_index = self.index_of(item)
        self.items.pop(item_index)

    def go_to_next(self):
        item = self.get_item(self._current_index + 1)
        if item is not None:
            self._current_index += 1
        elif self.items:
            if self.on_bottom_edge is not None:
                self.on_bottom_edge()
                return
            else:
                item = self.items[-1]
        return item

    def go_to_prev(self):
        prev_index = self._current_index - 1
        if prev_index >= 0:
            item = self.get_item(prev_index)
            if item is not None:
                self._current_index = prev_index
        else:
            if self.on_top_edge is not None:
                self.on_top_edge()
                return
            elif len(self.items) > 0:
                item = self.items[0]
        return item


class MenuItemObject(KeyboardNavigableNVDAObjectMixin, NVDAObject):
    role = controlTypes.Role.MENUITEM

    def __init__(self, parent, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.processID = self.parent.processID
        self.name = name
        if self.parent.use_default_navigation_scripts:
            self._gestureMap.update(
                {
                    "kb:downarrow": self.script_go_next,
                    "kb:uparrow": self.script_go_prev,
                }
            )

    def script_go_next(self, gesture):
        self.go_to_next()

    def script_go_prev(self, gesture):
        self.go_to_prev()

    @property
    def positionInfo(self):
        return {
            "indexInGroup": self.parent.index_of(self) + 1,
            "similarItemsInGroup": len(self.parent),
        }

    def go_to_next(self):
        item = self.parent.go_to_next()
        if item is not None:
            eventHandler.queueEvent("gainFocus", item)

    def go_to_prev(self):
        item = self.parent.go_to_prev()
        if item is not None:
            eventHandler.queueEvent("gainFocus", item)

    @script(gesture="kb:escape")
    def script_close_menu(self, gesture):
        self.parent.close_menu()

    @script(gesture="kb:enter")
    def script_activate_item(self, gesture):
        self.parent.on_item_activated(self)


class MenuObject(KeyboardNavigableNVDAObjectMixin, ItemContainerMixin, NVDAObject):
    role = controlTypes.Role.MENU
    use_default_navigation_scripts = True

    def __init__(self, name, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.parent = parent or api.getFocusObject()
        self.processID = self.parent.processID

    def close_menu(self):
        eventHandler.queueEvent("gainFocus", self.parent)

    def event_gainFocus(self):
        speech.speakObject(self, controlTypes.OutputReason.FOCUS)
        eventHandler.queueEvent("gainFocus", self.get_current_item())


class SimpleListItem(MenuItemObject):
    role = controlTypes.Role.LISTITEM

    def __init__(self, *args, close_gesture, **kwargs):
        super().__init__(*args, **kwargs)
        self.bindGesture(close_gesture, "close_menu")

    def script_close_menu(self, gesture):
        self.parent.close_menu()


class SimpleList(MenuObject):
    role = controlTypes.Role.LIST

    def __init__(self, *args, close_gesture, **kwargs):
        super().__init__(*args, **kwargs)
        self.close_gesture = close_gesture
        self.init_container_state(
            items=[],
            on_top_edge=self.onEdge,
            on_bottom_edge=self.onEdge,
        )

    def event_gainFocus(self):
        self.set_current(0)
        super().event_gainFocus()
        queueHandler.queueFunction(
            queueHandler.eventQueue, GameSound.score_list_open.play
        )

    def close_menu(self):
        super().close_menu()
        queueHandler.queueFunction(
            queueHandler.eventQueue, GameSound.score_list_close.play
        )

    def onEdge(self):
        GameSound.invalid.play()
        eventHandler.queueEvent("gainFocus", self.get_current_item())

    def add_item(self, item_text):
        self.items.insert(
            0,
            SimpleListItem(
                parent=self, name=item_text, close_gesture=self.close_gesture
            ),
        )

    def clear(self):
        self.init_container_state(
            items=[],
            on_top_edge=self.onEdge,
            on_bottom_edge=self.onEdge,
        )
