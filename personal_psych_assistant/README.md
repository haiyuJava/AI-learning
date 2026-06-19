# 本地私人心理助手原型

这是一个本地私人心理知识库原型：它会把 `data/thinking-notes` 编译成 `data/personal-psychology-wiki`，再基于这个 Wiki 做文本召回和心理辅助。

## 生成知识库

```powershell
.\.venv\Scripts\python.exe -m personal_psych_assistant.knowledge
```

## 文本测试

```powershell
.\.venv\Scripts\python.exe -m personal_psych_assistant.assistant --rebuild "我现在很焦虑，担心未来失控"
```

## 相似经历召回

当你焦虑时，更推荐用这个模式。它不会安慰你，而是从本地知识库里找你过去遇到过的相似场景、当时的处理方式和已经验证过的确定感。

```powershell
.\.venv\Scripts\python.exe -m personal_psych_assistant.recall --rebuild "我现在担心工作和未来不稳定，很焦虑"
```

现在召回是 profile 驱动的：先识别焦虑类型，再按该类型的主题、反向链接和优先来源加权召回，不是把关键词片段硬拼起来。可编辑配置在：

```text
data/personal-psychology-wiki/profiles/
  work.json
  relationship.json
  general.json
```

每个 profile 可以迭代这些字段：

- `triggers`：触发词
- `linked_themes`：关联到编译后的主题页
- `preferred_sources`：该焦虑类型优先召回的历史文章
- `certainty`：你认可的确定感模板
- `actions`：当下动作
- `avoid`：不适合的回应

## 数据边界

- 原始资料仍在 `data/thinking-notes`。
- 生活杂谈中的 `assets` 不作为知识输入。
- 编译后的 Wiki 在 `data/personal-psychology-wiki`。
- 当前版本不调用远程模型，不上传你的随笔。
- 这个助手只能做情绪支持和自我整理，不能替代专业心理咨询或医疗帮助。
