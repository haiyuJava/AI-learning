# 《流畅的 Python》第二版 8.3 渐进式类型实践学习笔记

> 说明：这里整理的是对“渐进式类型实践”这一节的理解型讲解，方便复习，不是书中原文摘录。

## 1. 这一节主要讲什么

8.2 主要解释“渐进式类型”是什么，8.3 则更偏向实践：在真实 Python 代码中，应该怎样逐步使用类型提示。

这一节的核心不是介绍某一个复杂类型语法，而是强调一种实践态度：

> 类型提示应该逐步添加，优先服务于可读性、工具检查和维护成本，而不是追求形式上的“全量标注”。

换句话说，Python 的类型提示不是为了把 Python 变成完全静态类型语言，而是为了让代码中最重要、最容易出错、最需要协作的部分变得更清晰。

## 2. 渐进式类型实践的基本思路

在实践中，不建议一开始就给所有变量、所有表达式、所有中间值都写类型。更合理的顺序是：

1. 先标注函数签名。
2. 再标注公共接口。
3. 再处理核心业务逻辑。
4. 最后根据类型检查器反馈补充必要的局部类型。

函数签名最值得优先标注，因为它是模块之间、函数之间协作的边界。

```python
def parse_token(token: str) -> dict[str, str]:
    ...
```

这个签名能直接告诉调用者：

- 需要传入字符串。
- 返回一个键和值都是字符串的字典。
- 函数的输入输出边界比较明确。

相比之下，函数内部的临时变量未必都需要显式标注，因为类型检查器通常可以根据上下文自动推断。

## 3. 类型检查器是实践的重要组成部分

类型提示本身只是语法，真正发挥作用需要配合类型检查工具。

常见工具包括：

- `mypy`
- `pyright`
- 编辑器或 IDE 内置类型分析

类型检查器的作用是：在代码运行前，尽量发现参数类型、返回值类型、属性访问、容器元素类型等方面的问题。

例如：

```python
def repeat(text: str, times: int) -> str:
    return text * times

repeat("ha", "3")
```

这段代码运行前，类型检查器就可以发现第二个参数应该是 `int`，但传入了 `str`。

所以 8.3 的实践重点之一是：类型提示不是孤立存在的，它要和类型检查工具一起使用。

### 3.1 `mypy` 是用来检查类型提示的

`mypy` 是 Python 里常见的静态类型检查工具。它不会运行你的程序，而是读取代码和类型注解，分析有没有类型不匹配的问题。

比如有一个文件 `demo.py`：

```python
def repeat(text: str, times: int) -> str:
    return text * times

repeat("ha", "3")
```

代码本身能被 Python 解释器读取，但类型上有问题：`times` 标注为 `int`，调用时却传入了字符串 `"3"`。

运行 `mypy`：

```bash
mypy demo.py
```

它会提示类似这样的错误：

```text
Argument 2 to "repeat" has incompatible type "str"; expected "int"
```

这说明 `mypy` 的重点是“运行前发现类型问题”。它适合检查：

- 函数参数类型是否传错。
- 函数返回值是否符合标注。
- `None` 是否被正确处理。
- 容器里的元素类型是否一致。
- 对象是否真的有你访问的属性或方法。

注意：`mypy` 不关心业务逻辑是否正确。它只检查类型层面的合理性。

例如：

```python
def discount(price: float, rate: float) -> float:
    return price + rate
```

这个函数从类型上看没有问题，两个 `float` 返回一个 `float`。但业务上折扣公式可能写错了。这个错误 `mypy` 不一定能发现。

### 3.2 `pytest` 是用来检查程序行为的

`pytest` 是 Python 常用的测试框架。它和 `mypy` 的关注点不同：`pytest` 会真正运行代码，通过断言检查结果是否符合预期。

例如有一个文件 `calc.py`：

```python
def discount(price: float, rate: float) -> float:
    return price * rate
```

可以写一个测试文件 `test_calc.py`：

```python
from calc import discount


def test_discount() -> None:
    assert discount(100.0, 0.8) == 80.0
```

运行测试：

```bash
pytest
```

如果函数行为正确，测试通过；如果你把函数写成 `return price + rate`，类型仍然可能没问题，但 `pytest` 会发现结果不对。

所以可以这样理解：

- `mypy` 检查“类型有没有传错”。
- `pytest` 检查“程序行为是不是对的”。
- 两者不是替代关系，而是互补关系。

### 3.3 `pytest` 和 `mypy` 如何配合

在渐进式类型实践中，一个常见工作流是：

1. 给关键函数加类型提示。
2. 用 `mypy` 检查类型是否一致。
3. 用 `pytest` 检查实际行为是否符合预期。
4. 根据错误提示修正类型标注或代码逻辑。

例如：

```python
def normalize_name(name: str) -> str:
    return name.strip().title()
```

对应测试：

```python
from users import normalize_name


def test_normalize_name() -> None:
    assert normalize_name("  ada lovelace ") == "Ada Lovelace"
```

此时两类工具分别负责：

- `mypy users.py`：检查 `normalize_name` 的参数和返回值类型。
- `pytest`：检查传入 `"  ada lovelace "` 后，结果是不是 `"Ada Lovelace"`。

如果调用时写错：

```python
normalize_name(123)
```

`mypy` 可以提前发现：参数应该是 `str`，不是 `int`。

如果实现时写错：

```python
def normalize_name(name: str) -> str:
    return name.strip()
```

类型没有错，但行为不符合预期，`pytest` 会发现没有执行 `.title()`。

### 3.4 初学时可以怎么运行

如果项目里已经安装了 `pytest` 和 `mypy`，通常可以直接运行：

```bash
pytest
mypy .
```

含义是：

- `pytest`：自动寻找 `test_*.py` 或 `*_test.py` 这类测试文件并运行。
- `mypy .`：检查当前目录下的 Python 代码类型。

如果只想检查一个文件：

```bash
mypy demo.py
```

如果只想运行一个测试文件：

```bash
pytest test_calc.py
```

如果只想运行某个测试函数：

```bash
pytest test_calc.py::test_discount
```

初学阶段不用一开始就配置很复杂。先理解这两个命令的区别最重要：

```bash
mypy your_file.py
pytest
```

一个做静态类型检查，一个做运行时行为测试。

## 4. 不要过度标注局部变量

Python 的类型系统支持给变量写注解：

```python
count: int = 0
name: str = "Guido"
```

但实践中不需要对每个局部变量都这样写。很多时候，类型检查器可以自动推断：

```python
count = 0
name = "Guido"
```

这里 `count` 和 `name` 的类型已经很明显，额外标注反而会增加噪声。

更适合显式标注局部变量的场景包括：

- 初始值无法表达真实类型。
- 空容器需要说明元素类型。
- 类型检查器无法准确推断。
- 代码读者需要额外提示。

例如空列表：

```python
names: list[str] = []
```

如果只写：

```python
names = []
```

类型检查器可能无法知道这个列表以后应该存放什么元素。

## 5. 容器类型要写清元素类型

只写 `list`、`dict` 通常信息不够完整。

不够清晰的写法：

```python
def load_users() -> list:
    ...
```

更清晰的写法：

```python
def load_users() -> list[str]:
    ...
```

如果结构更复杂，也可以继续写清楚：

```python
def load_scores() -> dict[str, int]:
    ...
```

这些类型提示可以帮助调用者理解：

- 列表中放的是什么。
- 字典的键和值分别是什么。
- 函数返回的数据结构应该如何使用。

在 Python 3.9 之后，常见内置容器可以直接写成：

```python
list[str]
dict[str, int]
tuple[str, int]
set[float]
```

不再必须写成 `typing.List`、`typing.Dict` 这类旧风格。

## 6. 优先标注接口，而不是实现细节

渐进式类型实践中，一个重要原则是：

> 类型提示首先应该描述“对外承诺”，而不是把内部实现写死。

例如，一个函数只需要遍历参数，那么不应该强行要求它接收 `list`：

```python
def total(numbers: list[float]) -> float:
    return sum(numbers)
```

这个写法能用，但限制比较死。更合理的是写成：

```python
from collections.abc import Iterable

def total(numbers: Iterable[float]) -> float:
    return sum(numbers)
```

这样调用者可以传入：

```python
total([1.0, 2.0])
total((1.0, 2.0))
total(x * 0.5 for x in range(10))
```

这个例子体现了 Python 类型提示的实践风格：不要因为加了类型提示，就放弃 Python 原本的鸭子类型思想。

## 7. `Optional` 和 `None` 要写清楚

如果一个值可能是 `None`，类型提示中应该明确表达出来。

例如：

```python
def find_user(name: str) -> str | None:
    ...
```

这表示函数可能返回字符串，也可能返回 `None`。

调用者看到这个签名后，就应该处理找不到的情况：

```python
user = find_user("Ana")
if user is None:
    print("not found")
else:
    print(user.upper())
```

这类标注很有价值，因为 `None` 相关错误在实际 Python 项目中很常见。

在旧版本写法中，也可能看到：

```python
from typing import Optional

def find_user(name: str) -> Optional[str]:
    ...
```

现代 Python 更常用 `str | None` 这种写法。

## 8. `Any` 应该作为过渡工具，而不是默认选择

`Any` 在渐进式类型中很重要，因为它允许你先跳过某些暂时难以标注的部分。

```python
from typing import Any

def dump(value: Any) -> None:
    print(value)
```

但实践中要注意：`Any` 会削弱类型检查。它相当于告诉类型检查器：“这里不要严格检查。”

适合使用 `Any` 的场景：

- 迁移旧代码时先占位。
- 处理未知结构的 JSON 数据。
- 调用缺少类型信息的第三方库。
- 写调试、日志、通用工具函数。

不适合滥用 `Any` 的场景：

- 核心业务模型。
- 公共 API。
- 明确知道类型却懒得写。
- 为了绕过类型检查器报错。

实践中可以先用 `Any` 让迁移跑起来，然后逐步收窄类型。

## 9. 类型别名可以提升可读性

当类型结构比较长时，可以使用类型别名。

直接写复杂类型：

```python
def summarize(records: list[dict[str, str | int]]) -> dict[str, int]:
    ...
```

使用类型别名：

```python
Record = dict[str, str | int]

def summarize(records: list[Record]) -> dict[str, int]:
    ...
```

类型别名的作用是让复杂类型更像领域概念，降低阅读压力。

不过也不要为了很简单的类型创建别名，否则会让代码绕一圈才看懂。

## 10. 类型提示应该帮助测试，而不是替代测试

类型检查可以发现一些问题，但它不能替代测试。

例如：

```python
def discount(price: float, rate: float) -> float:
    return price * rate
```

类型检查器只能知道 `price` 和 `rate` 是浮点数，但它不知道：

- `rate` 是否应该在 0 到 1 之间。
- `price` 是否允许为负数。
- 折扣公式是否符合业务规则。

这些仍然需要测试和运行时校验。

所以实践中的正确关系是：

- 类型提示负责描述接口和发现类型错误。
- 测试负责验证行为和业务规则。
- 运行时校验负责处理外部输入和不可信数据。

对应到工具上，可以简单记成：

- `mypy` 主要对应“类型提示和类型检查”。
- `pytest` 主要对应“测试和行为验证”。

## 11. 什么时候最应该加类型提示

实际项目中，可以优先给这些地方加类型提示：

1. 被很多地方调用的函数。
2. 公共模块和公共 API。
3. 数据处理入口和出口。
4. 容易传错参数的函数。
5. 返回值结构复杂的函数。
6. 和外部系统交互的边界代码。
7. 准备重构的代码。

这些地方加类型提示，收益通常最大。

相对来说，这些地方可以放宽：

1. 一次性脚本。
2. 实验代码。
3. 很短的私有辅助函数。
4. 逻辑非常直接、类型一眼可见的局部变量。

这就是“渐进式”的现实意义：把精力花在最有价值的位置。

## 12. 一个完整的小例子

没有类型提示的版本：

```python
def get_active_users(users):
    result = []
    for user in users:
        if user["active"]:
            result.append(user["name"])
    return result
```

加上类型提示：

```python
from collections.abc import Iterable

User = dict[str, str | bool]

def get_active_users(users: Iterable[User]) -> list[str]:
    result: list[str] = []
    for user in users:
        if user["active"]:
            result.append(str(user["name"]))
    return result
```

这个版本表达了几个信息：

- `users` 可以是任何可迭代对象，不一定必须是列表。
- 每个用户对象是一个字典。
- 字典的值可能是字符串或布尔值。
- 函数返回活跃用户的名字列表。
- 空列表 `result` 被明确标注为 `list[str]`。

不过这个例子也暴露了一个实践问题：用普通字典描述结构化数据并不总是最理想。真实项目中，可能会进一步使用 `TypedDict`、`dataclass` 或专门的数据模型来表达用户结构。

## 13. 实践中的常见误区

### 13.1 把类型提示当成运行时检查

类型提示默认不会阻止错误类型传入。要想在运行时检查外部输入，仍然需要显式校验或使用相关库。

### 13.2 为了类型检查写得过度复杂

如果类型提示比业务代码还难懂，就要重新考虑是否值得这样写。

### 13.3 只写形式，不跑类型检查器

只写注解但不使用 `mypy` 或 `pyright`，收益会明显下降。

### 13.4 过度使用具体类型

例如能接受任意可迭代对象时，却写死成 `list`。这会降低函数的通用性。

### 13.5 滥用 `Any`

`Any` 可以帮你过渡，但不能成为默认逃避方式。

## 14. 总结

8.3 “渐进式类型实践”的重点是：类型提示要服务于真实开发，而不是为了标注而标注。

实践时可以记住这几个原则：

1. 先标注函数签名和公共接口。
2. 容器类型要写清楚元素类型。
3. 可能为 `None` 的地方要明确写出来。
4. 能用抽象类型表达能力时，不要过早写死具体类型。
5. `Any` 用来过渡，不要滥用。
6. 类型检查器、测试、运行时校验各有职责。

好的渐进式类型实践应该让代码更清楚、更容易维护，而不是让代码变得僵硬和难读。
