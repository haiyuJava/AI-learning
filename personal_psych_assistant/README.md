# 本地私人心理助手原型

这是一个本地私人心理知识库原型：它会把 `data/thinking-notes`下的日志随笔，公众号文章编译成 `data/personal-psychology-wiki`，再基于这个 Wiki 做文本召回和心理辅助。

下面这些都是仓库根目录里的 Windows `.cmd` 包装器，直接在终端里运行即可。

如果你要放私有密钥，就复制根目录里的 `.env.local.example` 为 `.env.local`，然后填入自己的值。所有 `.cmd` 启动器都会自动读取它。

## 目录结构

```text
personal_psych_assistant/
  core/       # 召回与最终回答
  knowledge/  # 原始资料摄取、知识编译、profile 默认配置
  llm/        # OpenAI/DeepSeek/本地模板 provider
  ops/        # 沟通日志、知识库版本管理
  eval/       # 回归测试 runner 和 fixtures
  prompts/    # 可维护 prompt 模板
```

## 生成知识库

```powershell
.\knowledge.cmd
```

## 文本测试

```powershell
.\assistant.cmd --rebuild "我现在很焦虑，担心未来失控"
```

## 相似经历召回

当你焦虑时，更推荐用这个模式。它不会安慰你，而是从本地知识库里找你过去遇到过的相似场景、当时的处理方式和已经验证过的确定感。

```powershell
.\recall.cmd --rebuild "我现在担心工作和未来不稳定，很焦虑"
```

## 最终回答

`answer` 会先做 profile 分类和历史经验召回，再通过模型适配层生成最终回答。默认配置使用本地模板，不依赖任何云模型。

```powershell
.\answer.cmd "我现在对工作非常焦虑，我该怎么办"
```

模型配置在：

```text
personal_psych_assistant/llm/config.json
```

可参考：

```text
personal_psych_assistant/llm/config.example.json
```

支持 OpenAI、DeepSeek 以及本地模板兜底。云模型不可用时，会自动 fallback 到后续 provider；所有 provider 都不可用时使用本地模板。

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

## Prompt 模板

最终回答 prompt 在：

```text
personal_psych_assistant/prompts/answer.md
```

它固定了回答结构：用户问题、焦虑类型、确定感、历史经验、动作、避免事项和输出要求。不同模型共用同一套业务输入，便于维护和迭代。

## 测试集

回归测试在：

```text
personal_psych_assistant/tests/fixtures/recall_cases.json
```

运行：

```powershell
.\tests.cmd
```

测试会检查 profile 分类和关键认知是否丢失。需要测试最终回答 provider 时：

```powershell
.\tests.cmd --llm
```

## 知识库版本管理

知识库更新建议通过 Git 版本记录。当前工具会在 `data/personal-psychology-wiki/changelog/` 生成 changelog，并在 `data` 仓库中提交知识库变更。

```powershell
.\kb.cmd status
.\kb.cmd commit "更新工作焦虑 profile"
.\kb.cmd list
.\kb.cmd diff <commit>
.\kb.cmd rollback <commit>
```

## 沟通日志

系统会把通过 `answer` 产生的问题和回答追加到：

```text
data/personal-psychology-wiki/conversation-log/YYYY-MM.md
```

也可以手动追加：

```powershell
.\log.cmd --role user "这里写沟通内容"
```

## 数据边界

- 原始资料仍在 `data/thinking-notes`。
- 生活杂谈中的 `assets` 不作为知识输入。
- 编译后的 Wiki 在 `data/personal-psychology-wiki`。
- 当前版本不调用远程模型，不上传你的随笔。
- 这个助手只能做情绪支持和自我整理，不能替代专业心理咨询或医疗帮助。
