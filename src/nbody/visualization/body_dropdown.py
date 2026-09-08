"""Small scrollable dropdown rendered inside a Matplotlib figure."""

import numpy as np
from matplotlib.widgets import Button


class BodyDropdown:
    """Select any body index; duplicate names remain distinct by row number."""

    def __init__(self, figure, labels, callback):
        self.figure, self.labels, self.callback = figure, list(labels), callback
        self.selected = 0
        self.offset = 0
        self.page_size = 8
        self.open = False
        self.button = Button(figure.add_axes([0.68, 0.42, 0.29, 0.035]),
                             self._caption(), color="#243650", hovercolor="#344966")
        self.axes = figure.add_axes([0.68, 0.12, 0.29, 0.29], zorder=20, facecolor="#1b2d44")
        self.axes.set_visible(False)
        self.button.on_clicked(self.toggle)
        figure.canvas.mpl_connect("button_press_event", self._click)
        figure.canvas.mpl_connect("scroll_event", self._scroll)

    def _caption(self):
        return f"{self.selected+1}. {self.labels[self.selected]}  [v]"

    def toggle(self, event=None):
        self.open = not self.open
        self.axes.set_visible(self.open)
        self._draw()

    def _draw(self):
        self.axes.clear()
        self.axes.set_facecolor("#1b2d44")
        self.axes.set(xlim=(0, 1), ylim=(0, self.page_size+1), xticks=[], yticks=[])
        for row, index in enumerate(range(self.offset, min(len(self.labels), self.offset+self.page_size))):
            self.axes.text(0.035, self.page_size-row-0.5,
                           f"{index+1}. {self.labels[index]}", va="center", fontsize=10,
                           color="#67dfc5" if index == self.selected else "#e6edf7", clip_on=True)
        self.axes.text(0.035, self.page_size+0.5, "Scroll for more bodies", color="#9cafc7", fontsize=9)
        self.figure.canvas.draw_idle()

    def set_selected(self, index):
        self.selected = index
        self.offset = max(0, min(index, len(self.labels)-self.page_size))
        self.button.label.set_text(self._caption())
        if self.open:
            self._draw()

    def _click(self, event):
        if not self.open:
            return
        if event.inaxes is self.axes and event.ydata is not None:
            row = int(np.floor(self.page_size-event.ydata))
            index = self.offset+row
            if 0 <= row < self.page_size and index < len(self.labels):
                self.open = False
                self.axes.set_visible(False)
                self.set_selected(index)
                self.callback(index)
        elif event.inaxes is not self.button.ax:
            self.open = False
            self.axes.set_visible(False)
            self.figure.canvas.draw_idle()

    def _scroll(self, event):
        if self.open and event.inaxes is self.axes:
            direction = -1 if event.button == "up" else 1
            self.offset = max(0, min(self.offset+direction, max(0, len(self.labels)-self.page_size)))
            self._draw()
