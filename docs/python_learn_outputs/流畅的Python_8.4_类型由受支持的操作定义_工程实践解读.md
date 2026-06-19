# 《流畅的Python（第2版）》8.4 类型由受支持的操作定义 ------ 工程实践解读

这一节 **8.4 类型由受支持的操作定义（Types Are Defined by Supported
Operations）** 是《流畅的Python》里非常重要的一个思想。

对于从 Java 转向 Python、并希望从事 AI
应用开发（RAG、Agent）的开发者来说，这一节比语法本身更重要，因为它直接影响：

-   框架设计
-   Agent 开发
-   LangChain 源码阅读
-   Python 工程实践
-   避免大量类型判断造成的烂代码

------------------------------------------------------------------------

# 一、Java思维：看继承关系

Java程序员通常这样思考：

``` java
if(obj instanceof List){
    ...
}

if(obj instanceof ArrayList){
    ...
}
```

关注的是：

> 你是谁？

即：

``` text
ArrayList
    ↓
List
    ↓
Collection
```

通过继承树判断能力。

------------------------------------------------------------------------

# 二、Python思维：看能干什么

Python更关心：

> 你会干什么？

而不是：

> 你是谁？

例如：

``` python
class Duck:
    def quack(self):
        print("嘎嘎")

class Person:
    def quack(self):
        print("模仿鸭子")
```

函数：

``` python
def make_noise(obj):
    obj.quack()
```

调用：

``` python
make_noise(Duck())
make_noise(Person())
```

都能运行。

因为：

``` text
Duck 能 quack
Person 能 quack

=> 都可以传进去
```

这就是 Duck Typing（鸭子类型）。

经典定义：

> If it walks like a duck and quacks like a duck, it's a duck.

------------------------------------------------------------------------

# 三、工程实践中的巨大价值

假设你在做 RAG 系统。

需要处理：

``` text
pdf文件
word文件
markdown文件
html文件
```

Java新人写法：

``` python
if isinstance(loader, PdfLoader):
    ...
elif isinstance(loader, WordLoader):
    ...
elif isinstance(loader, MarkdownLoader):
    ...
```

Python高手写法：

统一约定：

``` python
load()
```

接口。

``` python
class PdfLoader:
    def load(self):
        ...

class WordLoader:
    def load(self):
        ...

class HtmlLoader:
    def load(self):
        ...
```

使用：

``` python
def process(loader):
    docs = loader.load()
```

不关心：

``` text
你是什么类型
```

只关心：

``` text
你有没有 load()
```

------------------------------------------------------------------------

# 四、LangChain大量使用这个思想

例如：

``` python
PyPDFLoader
Docx2txtLoader
TextLoader
```

全部支持：

``` python
load()
```

所以直接：

``` python
loader.load()
```

而不需要大量类型判断。

------------------------------------------------------------------------

# 五、Agent开发里的真实例子

假设你写工具：

``` python
SearchTool
BrowserTool
DatabaseTool
```

Java思维：

``` python
if isinstance(tool, SearchTool):
    ...
```

Python思维：

所有工具统一支持：

``` python
run()
```

调用时：

``` python
tool.run()
```

Agent根本不关心工具具体是什么。

------------------------------------------------------------------------

# 六、为什么大量 isinstance 是坏味道

例如：

``` python
def process(obj):

    if isinstance(obj, list):
        ...
    elif isinstance(obj, tuple):
        ...
    elif isinstance(obj, set):
        ...
```

说明你关注的是：

``` text
类型
```

而实际上应该关注：

``` text
是否可迭代
```

更好的写法：

``` python
for item in obj:
    ...
```

只要支持迭代即可。

------------------------------------------------------------------------

# 七、真实踩坑案例

错误设计：

``` python
def save(data):
    print(data["name"])
```

调用：

``` python
save({"name":"Tom"})
```

后来变成：

``` python
class User:
    name = "Tom"
```

再调用：

``` python
save(User())
```

直接报错。

原因：

``` text
代码假设 data 一定是 dict
```

更好的设计：

``` python
class User:

    def get_name(self):
        return self.name
```

``` python
def save(obj):
    print(obj.get_name())
```

关注能力，而不是具体类型。

------------------------------------------------------------------------

# 八、Python标准库中的体现

例如：

``` python
len(obj)
```

很多人以为只能用于：

``` python
list
tuple
str
```

实际上任何对象只要实现：

``` python
__len__()
```

即可。

例如：

``` python
class Team:

    def __len__(self):
        return 10
```

``` python
len(Team())
```

输出：

``` text
10
```

说明：

``` text
类型不是由继承决定
而是由行为决定
```

------------------------------------------------------------------------

# 九、AI工程中的经典场景

Embedding模型可能来自：

-   OpenAI
-   BGE
-   Jina

统一约定：

``` python
class EmbeddingModel:

    def embed(self, text):
        ...
```

RAG代码：

``` python
vector = model.embed(text)
```

无需：

``` python
if model == OpenAI:
    ...
```

实现了解耦。

------------------------------------------------------------------------

# 十、这一节真正想教你的

核心思想：

> Don't ask what an object is. Ask what it can do.

不要问：

``` text
这个对象是什么？
```

而要问：

``` text
这个对象能做什么？
```

------------------------------------------------------------------------

# 对RAG和Agent开发的启示

对于未来的AI应用开发：

``` text
Chunk是什么不重要
Embedding模型是什么不重要
向量库是什么不重要
LLM是什么不重要

只要支持约定好的操作即可。
```

这也是后来：

-   ABC（抽象基类）
-   Protocol
-   BaseLoader
-   BaseRetriever
-   BaseTool

等设计思想的重要基础。

在阅读 LangChain、LangGraph、LlamaIndex、OpenAI Agents SDK
等框架源码时，你会不断看到这种设计理念。
