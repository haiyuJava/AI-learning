# 《流畅的 Python》第二版 8.4 类型由受支持的操作定义学习笔记

> 说明：这里整理的是对“类型由受支持的操作定义”这一节的理解型讲解，重点补充工程实践中的例子和避坑经验，不是书中原文摘录。

## 1. 这一节主要讲什么

8.4 的核心思想可以概括成一句话：

> 在 Python 中，类型不只由类名决定，更重要的是对象支持哪些操作。

这其实就是 Python 常说的“鸭子类型”思想：

> 如果一个对象能像鸭子一样走路、像鸭子一样叫，那么它就可以被当成鸭子使用。

放到代码里就是：

> 如果一个对象支持某个函数需要的操作，那么它就可以作为这个函数的参数，而不必非得是某个具体类的实例。

比如一个函数只需要遍历参数：

```python
def print_items(items):
    for item in items:
        print(item)
```

这个函数真正需要的不是 `items` 必须是 `list`，而是 `items` 必须“可迭代”。所以 `list`、`tuple`、`set`、生成器都可以传进去。

## 2. “类型由操作定义”是什么意思

很多语言中，我们容易把类型理解成“类名”：

```python
isinstance(x, list)
```

但在 Python 的很多场景里，更重要的问题是：

- 这个对象能不能被迭代？
- 这个对象能不能用 `len()`？
- 这个对象能不能用 `[]` 取值？
- 这个对象能不能调用 `.read()`？
- 这个对象能不能调用 `.items()`？
- 这个对象能不能参与加法、比较、排序？

也就是说，函数真正依赖的是对象的“能力”，而不是对象的“身份”。

例如：

```python
def first(items):
    return items[0]
```

这个函数需要的能力是：

- 支持 `items[0]` 这种下标访问。

它不一定要求 `items` 是 `list`。`tuple`、`str` 也支持这个操作。

再看：

```python
def total(numbers):
    return sum(numbers)
```

这个函数需要的能力是：

- `numbers` 可以被迭代。
- 迭代出来的元素可以被 `sum` 相加。

它也不要求 `numbers` 必须是 `list`。

## 3. 类型提示应该描述“需要的操作”

这一节和类型提示联系起来后，重点是：

> 写类型提示时，不要过早写死具体类型，而应该尽量描述函数真正需要的操作。

不够好的写法：

```python
def total(numbers: list[float]) -> float:
    return sum(numbers)
```

这个函数只是遍历并求和，不需要修改列表，也不需要下标访问，所以写成 `list[float]` 限制太死。

更合理的写法：

```python
from collections.abc import Iterable

def total(numbers: Iterable[float]) -> float:
    return sum(numbers)
```

这表示：只要传进来的对象能迭代出 `float`，就可以使用。

工程上的好处是：

- 调用者可以传 `list`。
- 调用者可以传 `tuple`。
- 调用者可以传生成器。
- 调用者可以传数据库查询结果的迭代对象。
- 函数不和某个具体容器绑定。

## 4. 工程实践坑 1：参数写成 `list`，导致接口太死

很多初学者写类型提示时，会习惯把参数写成 `list`：

```python
def send_emails(emails: list[str]) -> None:
    for email in emails:
        send(email)
```

这在小脚本里没问题，但在工程中可能限制调用方。

比如调用方的数据可能来自：

```python
emails = ("a@example.com", "b@example.com")
```

或者来自生成器：

```python
def read_emails_from_file(path: str):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.strip()
```

如果 `send_emails` 只要求“能遍历”，更好的签名是：

```python
from collections.abc import Iterable

def send_emails(emails: Iterable[str]) -> None:
    for email in emails:
        send(email)
```

避坑原则：

> 如果函数只遍历参数，优先用 `Iterable[T]`，不要默认写 `list[T]`。

## 5. 工程实践坑 2：需要下标访问时误写成 `Iterable`

虽然不要过度写死具体类型，但也不能抽象过头。

错误示例：

```python
from collections.abc import Iterable

def get_first_name(names: Iterable[str]) -> str:
    return names[0]
```

问题在于：`Iterable[str]` 只保证对象能被 `for` 遍历，不保证支持 `names[0]`。

例如生成器是 `Iterable`，但不能用下标：

```python
names = (name for name in ["Ana", "Bob"])
names[0]  # TypeError
```

如果函数需要下标访问，应该使用更准确的抽象：

```python
from collections.abc import Sequence

def get_first_name(names: Sequence[str]) -> str:
    return names[0]
```

`Sequence` 表示序列，通常支持：

- 遍历
- `len()`
- 下标访问
- 切片

避坑原则：

> 类型提示要和函数实际使用的操作一致。只遍历用 `Iterable`；要下标和长度，考虑 `Sequence`。

## 6. 工程实践坑 3：函数修改了参数，却把类型写得太宽

再看一个反过来的问题。

错误示例：

```python
from collections.abc import Sequence

def add_default_tag(tags: Sequence[str]) -> None:
    tags.append("default")
```

问题在于：`Sequence` 只表示“可读序列”，不保证能修改。`tuple[str, ...]` 也是 `Sequence[str]`，但不能 `.append()`。

如果函数需要修改列表，应该写成：

```python
def add_default_tag(tags: list[str]) -> None:
    tags.append("default")
```

或者，如果你只需要“可变序列”的能力：

```python
from collections.abc import MutableSequence

def add_default_tag(tags: MutableSequence[str]) -> None:
    tags.append("default")
```

避坑原则：

> 如果函数会修改参数，类型提示必须表达“可变”这个能力。

在工程中，最好进一步思考：函数到底该不该修改传入参数？

很多时候，更安全的写法是返回新列表：

```python
from collections.abc import Iterable

def with_default_tag(tags: Iterable[str]) -> list[str]:
    return [*tags, "default"]
```
这段代码是一个 Python 函数，它的主要作用是：
接收一个包含字符串的旧列表（或任何可迭代对象），在其末尾添加一个 "default" 字符串，并返回一个全新的列表
*tags 的意思是：把 tags 里面的元素一个一个拆开、释放出来。

[*tags, "default"] 的意思是：创建一个新的列表，先把 tags 里拆出来的元素放进去，最后再在末尾追加一个 "default"。

这种写法副作用更少，调用者也更容易理解。

## 7. 工程实践坑 4：用 `dict` 写死配置结构

工程项目里很常见这种函数：

```python
def connect(config: dict[str, str]) -> None:
    host = config["host"]
    port = int(config["port"])
```

这个签名有几个问题：

- 它没有说明必须有哪些 key。
- 它假设所有 value 都是 `str`。
- 调用方不知道 `host`、`port` 是必需字段。
- 重构时容易出现 key 拼写错误。

如果只是读取映射，可以先把 `dict` 改成 `Mapping`：

```python
from collections.abc import Mapping

def connect(config: Mapping[str, str]) -> None:
    host = config["host"]
    port = int(config["port"])
```

`Mapping` 表示只读映射能力：支持按 key 取值、遍历 key、使用 `.items()` 等，但不要求一定是 `dict`。

如果配置结构固定，更推荐使用 `TypedDict`：

```python
from typing import TypedDict

class DbConfig(TypedDict):
    host: str
    port: int

def connect(config: DbConfig) -> None:
    host = config["host"]
    port = config["port"]
```

这样类型检查器可以知道：

- `host` 必须存在。
- `port` 必须存在。
- `host` 是 `str`。
- `port` 是 `int`。

避坑原则：

> 普通 `dict[str, object]` 或 `dict[str, Any]` 很容易让结构信息丢失。固定结构的数据优先考虑 `TypedDict`、`dataclass` 或专门的数据模型。

## 8. 工程实践坑 5：过度使用 `isinstance`

在 Python 中，下面这种写法经常让代码变僵硬：

```python
def export(data):
    if isinstance(data, list):
        for item in data:
            write(item)
    else:
        raise TypeError("data must be a list")
```

这个函数其实只需要 `data` 可迭代，不需要它必须是 `list`。

更 Pythonic 的写法是：

```python
from collections.abc import Iterable

def export(data: Iterable[str]) -> None:
    for item in data:
        write(item)
```

当然，这不是说 `isinstance` 不能用。它适合用于：

- 处理外部不可信输入。
- 运行时需要分支处理不同类型。
- 做参数校验并给出清晰错误。
- 和第三方边界交互。

但在内部业务逻辑中，过多 `isinstance` 往往说明接口设计不够抽象。

避坑原则：

> 内部函数优先依赖对象支持的操作；边界层再做必要的运行时类型校验。

## 9. 常用抽象类型如何选择

这些类型通常来自 `collections.abc`：

```python
from collections.abc import Iterable, Sequence, Mapping, MutableSequence, MutableMapping, Callable
```

常见选择可以这样记：

| 你需要的操作 | 推荐类型 |
| --- | --- |
| 只需要 `for` 遍历 | `Iterable[T]` |
| 需要下标、长度、遍历 | `Sequence[T]` |
| 需要只读 key-value 映射 | `Mapping[K, V]` |
| 需要修改 key-value 映射 | `MutableMapping[K, V]` |
| 需要追加、删除、修改序列 | `MutableSequence[T]` |
| 需要接收一个函数 | `Callable[[ArgType], ReturnType]` |

例子：

```python
from collections.abc import Callable, Iterable, Mapping, Sequence

def apply_discount(prices: Iterable[float], rate: float) -> list[float]:
    return [price * rate for price in prices]

def first_item(items: Sequence[str]) -> str:
    return items[0]

def get_header(headers: Mapping[str, str], name: str) -> str | None:
    return headers.get(name)

def transform(value: str, func: Callable[[str], str]) -> str:
    return func(value)
```

## 10. `Protocol`：用操作定义类型的更强工具

有时候，标准抽象类型还不够表达你需要的操作。

比如你想要一个对象，只要它有 `.close()` 方法就行，不关心它来自哪个类。

可以使用 `Protocol`：

```python
from typing import Protocol

class Closable(Protocol):
    def close(self) -> None:
        ...

def close_all(resources: Iterable[Closable]) -> None:
    for resource in resources:
        resource.close()
```

这个类型表达的就是：

> 只要对象有 `close() -> None` 这个方法，就可以传进来。

这非常符合“类型由受支持的操作定义”的思想。

工程中常见场景：

- 你不想让业务代码依赖某个具体第三方类。
- 你只关心对象有某几个方法。
- 你想提高测试替身、mock 对象的兼容性。
- 你希望接口更稳定，降低和具体实现的耦合。

例如文件上传逻辑：

```python
from typing import Protocol

class FileLike(Protocol):
    def read(self, size: int = -1) -> bytes:
        ...

def upload(file: FileLike) -> None:
    data = file.read()
    send_to_storage(data)
```

这样真实文件对象、内存中的 `BytesIO`、测试里的假对象，只要有 `read()` 方法，都可以使用。

避坑原则：

> 当函数只依赖对象的一小组方法时，可以考虑用 `Protocol` 描述这组方法，而不是依赖具体实现类。

## 11. 工程实践中的接口设计建议

写函数签名时，可以按这个顺序问自己：

1. 这个函数到底用了参数的哪些操作？
2. 只是遍历，还是需要下标？
3. 是只读，还是会修改？
4. 是普通容器，还是固定结构的数据？
5. 能否用 `Iterable`、`Sequence`、`Mapping` 这类抽象表达？
6. 是否需要用 `Protocol` 描述自定义能力？
7. 是否应该避免修改传入对象，改为返回新对象？

一个实用原则：

> 参数类型尽量写宽一点，返回类型尽量写具体一点。

例如：

```python
from collections.abc import Iterable

def normalize_names(names: Iterable[str]) -> list[str]:
    return [name.strip().title() for name in names]
```

这里参数写成 `Iterable[str]`，是为了允许更多输入；返回值写成 `list[str]`，是因为函数确实构造并返回了一个列表。

这种接口在工程中更好用：

- 调用方输入更自由。
- 函数返回更明确。
- 类型检查器更容易帮你发现错误。
- 减少不必要的类型转换。

## 12. 一个综合工程例子

假设你要写一个订单金额计算函数。

不够好的版本：

```python
def calc_total(items: list[dict[str, float]]) -> float:
    total = 0.0
    for item in items:
        total += item["price"] * item["quantity"]
    return total
```

问题：

- 参数被写死为 `list`，其实只需要遍历。
- `dict[str, float]` 没有表达必需字段。
- `quantity` 也许应该是 `int`，但被迫写成 `float`。
- key 写错时，类型检查器不一定能帮上忙。

更好的版本：

```python
from collections.abc import Iterable
from typing import TypedDict

class OrderItem(TypedDict):
    price: float
    quantity: int

def calc_total(items: Iterable[OrderItem]) -> float:
    total = 0.0
    for item in items:
        total += item["price"] * item["quantity"]
    return total
```

这个版本更符合工程实践：

- `items` 只要求可迭代。
- 每个订单项的结构清晰。
- `price` 和 `quantity` 类型明确。
- 调用方可以传列表、元组、生成器、查询结果。
- 类型检查器更容易发现字段和类型错误。

如果后续订单项变成类，也可以继续演进：

```python
from collections.abc import Iterable
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderItem:
    price: float
    quantity: int

def calc_total(items: Iterable[OrderItem]) -> float:
    return sum(item.price * item.quantity for item in items)
```

这就是“类型由操作定义”在工程中的价值：接口关注需要的能力，数据结构关注真实约束。

## 13. 这一节最重要的避坑总结

1. 不要一上来就把参数写死成 `list`、`dict`。
2. 函数只遍历参数时，优先考虑 `Iterable`。
3. 函数需要下标和长度时，考虑 `Sequence`。
4. 函数只读取映射时，用 `Mapping`；需要修改时才用 `MutableMapping`。
5. 函数会修改序列时，用 `MutableSequence` 或具体的 `list`。
6. 固定结构的数据不要长期用普通 `dict` 硬撑，考虑 `TypedDict` 或 `dataclass`。
7. 过多 `isinstance` 可能说明接口设计太依赖具体类。
8. 当你只需要某几个方法时，考虑用 `Protocol` 描述能力。
9. 参数类型通常可以抽象一些，返回类型通常应该具体一些。
10. 类型提示要和实际使用的操作一致，不能为了“看起来通用”而乱用抽象类型。

## 14. 总结

8.4 的核心是：Python 的类型观念和很多静态语言不同。真正重要的不是对象叫什么类名，而是对象支持哪些操作。

这个思想落实到类型提示和工程实践中，就是：

- 用类型提示描述函数真正依赖的能力。
- 不要把接口绑定到不必要的具体容器。
- 不要为了抽象而抽象，类型要匹配实际操作。
- 在固定数据结构、外部输入、复杂协作边界处，要用更精确的类型建模。

写得好的类型提示，应该让接口更灵活、约束更清楚、调用更安全，而不是让代码变得更死。
