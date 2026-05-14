# 第5课：分支

**预计时间：40分钟**

> **上节课回顾**：你学会了连接 GitHub，用 `git push` 和 `git pull` 同步代码。
>
> **本节课目标**：理解分支的概念 → 创建和切换分支 → 合并分支。

## 5.1 什么是分支？

**分支**就像在平行宇宙里开发——每个分支里做的事情互不影响。

```
main:      ○──○────────────○──────────
                \          /
feature:         ○──○──○──○
```

> **生活类比**：你在写文章时，保存了一份"副本"用来尝试新的写法，如果效果好就合并到正式稿，效果不好就扔掉。分支就是这个"副本"。

**为什么用分支？**
- 开发新功能时不影响主分支
- 多人同时做不同功能，互不干扰
- 修复紧急 Bug 时不会把没做完的新功能也发布出去

## 5.2 查看分支

```bash
# 查看所有本地分支（* 表示当前所在分支）
git branch

# 查看所有分支（包括远程）
git branch -a
```

## 5.3 创建和切换分支

```bash
# 创建一个新分支
git branch feature-login

# 切换到该分支
git checkout feature-login

# 或者一步到位：创建并切换
git checkout -b feature-login
```

> **解释**：`-b` 是 "branch" 的意思，表示创建并切换。

## 5.4 在不同分支上工作

现在我们在 `feature-login` 分支上做一些修改：

```bash
# 确认当前在 feature-login 分支
git branch

# 创建一个新文件
echo "登录功能开发中..." > login.txt

# 提交
git add login.txt
git commit -m "添加登录功能初版"
```

## 5.5 切换回 main 分支看看

```bash
# 切回 main 分支
git checkout main

# 看看 login.txt 在不在
ls login.txt
```

> 你会发现 `login.txt` **不存在**！因为它在 `feature-login` 分支上，`main` 分支看不到。这就是分支的"隔离"特性。

## 5.6 合并分支

把 `feature-login` 的内容合并到 `main`：

```bash
# 确保当前在 main 分支
git checkout main

# 合并 feature-login 分支
git merge feature-login
```

> 现在 `login.txt` 出现在 `main` 分支了。

## 5.7 删除分支

合并完成后，如果不再需要，可以删除分支：

```bash
# 删除本地分支
git branch -d feature-login

# 如果要删除还没合并的分支（强制删除）
git branch -D feature-login
```

## 5.8 分支的命名规范

好的分支名让人一看就懂：

```
feature/添加登录功能    # 新功能
bugfix/修复登录闪退     # 修 Bug
hotfix/紧急修复支付问题   # 紧急修复
```

创建合规范的分支：

```bash
git checkout -b feature/添加注册功能
```

## 5.9 实操练习：完整的分支流程

```bash
# 1. 在 main 上创建一个新分支
git checkout -b feature/添加个人信息

# 2. 创建文件并提交
echo "个人信息页面" > profile.txt
git add profile.txt
git commit -m "添加个人信息页面初版"

# 3. 再修改一次
echo "姓名、邮箱字段" >> profile.txt
git add .
git commit -m "完善个人信息字段"

# 4. 切回 main，合并
git checkout main
git merge feature/添加个人信息

# 5. 删除功能分支
git branch -d feature/添加个人信息
```

## ✅ 今日练习

1. 查看当前分支：`git branch`
2. 创建并切换到 `feature/我的第一个分支`
3. 在该分支上创建一个新文件 `hobby.txt`，写点你的兴趣爱好
4. 提交修改
5. 切回 `main`，确认看不到 `hobby.txt`
6. 将分支合并到 `main`
7. 确认 `hobby.txt` 出现了
8. 删除 `feature/我的第一个分支`

---

**完成了吗？进入 [第6课](./lesson-06.md)，学习多人协作中的冲突处理！**
