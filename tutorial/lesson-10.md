# 第10课：常用技巧与下一步方向

**预计时间：30分钟**

> **上节课回顾**：你完成了一个完整的实战项目。
>
> **本节课目标**：学习 Git 常用技巧 → 了解继续学习的方向。

## 10.1 Git 别名

把长命令变成短命令：

```bash
# 配置别名
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg "log --oneline --graph --all"

# 现在可以这样用
git st          # = git status
git co main     # = git checkout main
git br          # = git branch
git ci -m "xxx" # = git commit -m "xxx"
git lg          # = git log --oneline --graph --all
```

## 10.2 git stash — 临时保存

当你在分支上工作到一半，需要切换到其他分支时：

```bash
# 临时保存当前工作（工作区会变得干净）
git stash

# 查看暂存的工作
git stash list

# 恢复最近一次暂存
git stash pop

# 恢复但不删除暂存
git stash apply

# 丢弃暂存
git stash drop
```

**场景举例：**
1. 你在 `feature-a` 上开发到一半
2. 突然需要修复 main 上的一个紧急 Bug
3. `git stash` → 保存在一边
4. 切换到 main，修 Bug，提交
5. 切回 `feature-a`，`git stash pop` 继续开发

## 10.3 git log 进阶

```bash
# 图形化查看所有分支历史
git log --oneline --graph --all

# 查看某个文件的修改历史
git log -p hello.txt

# 显示每次修改的文件列表
git log --stat

# 搜索提交信息
git log --grep="登录"
```

## 10.4 git blame — 追责神器

```bash
# 查看文件的每行是谁修改的
git blame hello.txt
```

> 这不是用来"甩锅"的！而是当遇到问题，可以用它找到**熟悉那段代码的人**来请教。

## 10.5 处理错误

### 提交信息写错了

```bash
# 修改最近一次提交的信息
git commit --amend -m "正确的提交信息"
```

> ⚠️ 如果已经 push 到 GitHub 了，需要 `git push --force`（谨慎使用！）

### 忘记添加某个文件

```bash
git add 忘记的文件
git commit --amend --no-edit
```

> `--no-edit` 表示不修改提交信息。

### 远程仓库地址变了

```bash
# 修改远程仓库 URL
git remote set-url origin https://github.com/新地址/新仓库.git
```

## 10.6 可视化工具推荐

命令行熟悉后，可视化工具可以帮你更直观地理解：

- **VS Code 内置**：源代码管理图标（左边栏的"分支"图标）
- **GitHub Desktop**：GitHub 官方桌面客户端，适合初学者
- **Sourcetree**：免费的 Git 图形化工具
- **GitLens (VS Code 插件)**：在 VS Code 里显示详细的 Git 信息

## 10.7 继续学习的方向

你学完了 Git/GitHub 入门教程！接下来你有很多方向可以走：

### 如果你想学 Web 开发
- HTML → CSS → JavaScript
- 用 GitHub Pages 部署你的网页（免费！）

### 如果你想学 Python
- Python 基础语法
- 用 `pip` 管理包
- 尝试自动化脚本

### 如果你想进一步深造 Git
- **Rebase**：更高级的提交管理（`git rebase`）
- **Git Hooks**：自动化检查（比如提交前自动运行测试）
- **GitHub Actions**：自动化部署和测试

## ✅ 今日练习

1. 设置 Git 别名：`st`、`co`、`br`
2. 试试 `git stash`：在分支上修改文件但不提交，stash，恢复
3. 用 `git blame` 查看 README.md 每一行的作者
4. 用 `git lg` 查看这个仓库的完整历史

---

## 🎉 恭喜你完成了 Git/GitHub 入门教程！

你已经学会了：

| 技能 | 内容 |
|------|------|
| ✅ Git 基础 | init, add, commit, status |
| ✅ 查看和撤销 | log, diff, restore, reset |
| ✅ 远程仓库 | clone, push, pull, remote |
| ✅ 分支操作 | branch, checkout, merge |
| ✅ 解决冲突 | 冲突标记、手动解决 |
| ✅ Pull Request | 创建、Review、合并 |
| ✅ 最佳实践 | .gitignore、提交规范 |
| ✅ 实用技巧 | stash、alias、blame |

**现在，你可以选择你感兴趣的方向继续深入学习了！祝你编程之路顺利！🚀**

---

*有其他问题随时问我！*
