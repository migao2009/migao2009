# 第7课：Pull Request 工作流

**预计时间：40分钟**

> **上节课回顾**：你学会了解决合并冲突。
>
> **本节课目标**：理解 Pull Request → 在 GitHub 上创建 PR → Code Review。

## 7.1 什么是 Pull Request？

**Pull Request（PR）** 是一种"请求合并"的机制。你可以理解为：

> "我做好了一个功能，请查收。如果你觉得没问题，就把我的代码合并到主分支吧。"

**PR 的工作流程：**
1. 在分支上开发
2. 推送到 GitHub
3. 创建 Pull Request
4. 团队成员 Review 代码
5. 讨论 → 修改 → 确认
6. 合并到主分支

## 7.2 创建 Pull Request

### 步骤1：创建分支并推送

```bash
# 在 main 基础上创建新分支
git checkout -b feature/about-page

# 创建文件
echo "# 关于页面" > about.md
echo "这是我的学习项目。" >> about.md

# 提交
git add about.md
git commit -m "添加关于页面"

# 推送到远程
git push -u origin feature/about-page
```

### 步骤2：在 GitHub 上创建 PR

1. 推送完成后，GitHub 页面会出现一个 **"Compare & pull request"** 按钮 → 点击它
2. 如果没有，可以点击仓库页面的 **Pull requests** 标签 → **New pull request**
3. 确认：
   - **base**：`main`（要合并到的目标分支）
   - **compare**：`feature/about-page`（你的分支）
4. 填写 PR 信息：

```
标题：添加关于页面

描述：
- 新增 about.md，包含项目简介
- 使用 Markdown 格式
```

5. 点击 **Create pull request**

## 7.3 Code Review（代码审查）

PR 创建后，你可以邀请团队成员审查代码。

### 在 GitHub 上 Review 的步骤

1. 打开 PR 页面，点击 **Files changed** 标签
2. 查看改动的代码
3. 点击某行代码旁的 **+** 可以发表评论
4. 右上角点击 **Review changes**
   - **Comment**：一般评论
   - **Approve**：批准
   - **Request changes**：要求修改

### Code Review 注意事项

**作为提交者：**
- PR 不要太大（几百行 vs几千行），小 PR 更容易审查
- 写好 PR 描述，让 reviewer 知道改了什么、为什么

**作为审查者：**
- 关注"逻辑是否正确"，而不是"代码风格"
- 如果有疑问就问，不要猜测
- 指出问题也要肯定好的地方

## 7.4 合并 PR

Review 通过后，就可以合并了：

1. 在 PR 页面点击 **Merge pull request**
2. 点击 **Confirm merge**
3. 可选删除分支（Clean up）

### GitHub 上的合并方式有三种

| 方式 | 效果 | 适用场景 |
|------|------|----------|
| **Create a merge commit** | 保留所有提交历史 | 团队协作 |
| **Squash and merge** | 把所有提交压缩成一个 | 个人功能开发 |
| **Rebase and merge** | 保持线性历史 | 追求整洁历史 |

> 初学阶段用默认的 **Create a merge commit** 就好。

## 7.5 合并后在本地的操作

PR 在 GitHub 上合并后，本地也需要同步：

```bash
# 切回 main
git checkout main

# 拉取最新代码（包含了刚才合并的 PR）
git pull

# 删除本地分支（远程分支可以在 GitHub 上删除）
git branch -d feature/about-page
```

## ✅ 今日练习

1. 创建一个新分支 `feature/个人介绍`
2. 在该分支上创建 `intro.md`，写一段自我介绍
3. 推送分支到 GitHub
4. 在 GitHub 上创建 Pull Request
5. 自己 Review 自己的 PR（看看有没有要改的地方）
6. 合并 PR
7. 在本地 `git checkout main` 并 `git pull`，确认 `intro.md` 已合并

---

**完成了吗？进入 [第8课](./lesson-08.md)，学习 Git 最佳实践！**
