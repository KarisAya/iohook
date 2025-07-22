# OutHook

接管程序输出，并且在输出时触发回调。

# 安装

```bash
pipx install outhook
```

# 使用

```bash
outhook <command> [args]
# 例如 outhook java --version
```

在当前文件夹下创建一个文件 `hook.py`
定义一个函数 `callback` 参数如下

```python
def callback(line: bytes) -> None: ...
```

line 是输出的一行，bytes 类型。
