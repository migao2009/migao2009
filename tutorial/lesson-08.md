# 第8课：.gitignore 与最佳实践

**预计时间：30分钟**

> **上节课回顾**：你学会了 Pull Request 工作流。
>
> **本节课目标**：学会使用 .gitignore → 学习提交规范 → 养成好习惯。

## 8.1 什么是 .gitignore？

有些文件**不应该**被 Git 管理。例如：

- 密码/API 密钥等敏感信息
- 编译生成的中间文件（`.exe`, `.class`, `.dll`）
- 依赖包（`node_modules/`, `vendor/`）
- 系统文件（`.DS_Store`, `Thumbs.db`）
- IDE 配置文件（`.vscode/`, `.idea/`）

**`.gitignore`** 文件就是告诉 Git："忽略这些文件，别管它们。"

## 8.2 创建 .gitignore

```bash
# 在仓库根目录创建 .gitignore
echo "# 忽略所有 .log 文件" > .gitignore
echo "*.log" >> .gitignore
echo "" >> .gitignore
echo "# 忽略 node_modules 文件夹" >> .gitignore
echo "node_modules/" >> .gitignore
```

然后把 `.gitignore` 本身提交：

```bash
git add .gitignore
git commit -m "添加 .gitignore"
```

## 8.3 .gitignore 常用写法

```gitignore
# 忽略特定文件
secrets.txt

# 忽略所有 .log 结尾的文件
*.log

# 忽略文件夹
node_modules/
build/
dist/

# 忽略特定文件夹下的所有文件
logs/*.log

# 但保留某个文件（在忽略后例外）
!logs/important.log

# 忽略所有 .env 文件（敏感信息）
.env
.env.local
```

> 💡 GitHub 提供了各种项目的 `.gitignore` 模板：https://github.com/github/gitignore

## 8.4 已经提交的文件可以忽略吗？

如果你已经提交了一个文件（比如 `secrets.txt`），然后把它加到 `.gitignore`，**Git 仍然会跟踪它**。需要先移除：

```bash
# 从 Git 中删除文件但保留在本地（不删除实际文件）
git rm --cached secrets.txt

# 然后提交
git commit -m "停止跟踪 secrets.txt"
```

## 8.5 好的提交习惯

### 1. 提交要小，但要完整

- ✅ 一个提交只做一件事
- ✅ 提交应该是"完整的"（代码能正常工作）
- ❌ 一个提交改 20 个文件，修改不相干的内容

### 2. 经常提交

- 完成一个小功能就提交一次
- 不用担心提交太多——可以后面 squash（压缩）

### 3. 写好的提交信息

```
简洁标题（50字以内，句首大写，不用句号）

详细说明（可选，72字换行，解释为什么这么改）
```

GitHub 上常见的提交规范：

```
feat: 添加用户登录功能
fix: 修复登录按钮无响应的问题
docs: 更新 README 文档
refactor: 重构用户模块代码
test: 添加登录单元测试
chore: 更新依赖版本
```

## 8.6 开发流程检查清单

```
每天开始工作前：
☐ git pull（拉取最新代码）
☐ git checkout -b feature/xxx（创建功能分支）

开发过程中：
☐ git add 具体文件（不要无脑 git add .）
☐ git commit -m "描述"（经常提交）
☐ git push（推送到远程，可创建 PR）

提交代码前自查：
☐ 代码有没有测试过？
☐ 有没有包含敏感信息（密码、密钥）？
☐ 有没有不需要的文件（编译产物）？
☐ 提交信息有没有写清楚？
```

## ✅ 今日练习

1. 在当前仓库创建 `.gitignore`，忽略所有 `.log` 文件和 `temp/` 文件夹
2. 创建 `test.log` 文件，确认 `git status` 不再列出它
3. 创建 `temp/` 文件夹并在里面创建一个文件，确认被忽略
4. 提交 `.gitignore`
5. 把今天学到的提交规范用在提交信息上

---

**完成了吗？进入 [第9课](./lesson-09.md)，做一个实战项目！**
