from tqdm import tqdm


class ProgressBar():
    def __init__(self, step_size=100):
        self._step_size = step_size
        self._cur_bar = tqdm(step_size) if step_size > 0 else None
        self._cur_pos = 0
        self._total = 0

    def update(self):
        if self._cur_bar is None:
            return
        self._cur_pos = self._cur_pos + 1
        self._total = self._total + 1
        self._cur_bar.update(1)
        self._cur_bar.set_description_str('Processing: %s/%s,total: %s' % (self._cur_pos, self._step_size, self._total))
        if self._cur_pos == self._step_size:
            self.reset(self._step_size)

    def reset(self, total):
        if self._cur_bar is None:
            return
        self._cur_bar.reset(total)
        self._cur_pos = 0

    def close(self):
        if self._cur_bar is not None:
            self._cur_bar.close()
