# 第6课：协作与冲突

**预计时间：45分钟**

> **上节课回顾**：你学会了创建、切换、合并、删除分支。
>
> **本节课目标**：理解多人协作流程 → 制造冲突 → 解决冲突。

## 6.1 多人协作的标准流程

当多人一起开发时，一天的工作流程通常是这样的：

```bash
# 1. 开始工作前，先拉取最新代码
git pull

# 2. 创建功能分支
git checkout -b feature/xxx

# 3. 在分支上开发...
# 4. 提交
git add .
git commit -m "完成xxx功能"

# 5. 推送分支到远程
git push -u origin feature/xxx

# 6. 在 GitHub 上创建 Pull Request（下一课详细讲）
```

> 🔑 **重要习惯**：**每次开始工作前先 `git pull`**，确保你的代码是最新的。

## 6.2 什么是冲突？

**冲突**发生在两个人都修改了同一个文件的同一部分时，Git 不知道该用谁的版本。

举个例子：
1. 你和同事都从 `main` 创建了自己的分支
2. 你们都修改了 `index.html` 的第 10 行
3. 你的分支合并时，Git 发现第 10 行有两个不同的版本 → **冲突**

> **冲突不是错误！** 它很正常，解决就好了。

## 6.3 制造一个冲突（本地练习）

让我们在自己的电脑上模拟冲突场景：

### 步骤1：创建两个分支，各自修改

```bash
# 在 main 上创建一个文件
echo "第一行内容" > conflict.txt
git add conflict.txt
git commit -m "添加 conflict.txt"

# 创建分支 A 并修改
git checkout -b branch-a
echo "分支A修改的内容" >> conflict.txt
git add .
git commit -m "分支A的修改"

# 切回 main，创建分支 B
git checkout main
git checkout -b branch-b

# 修改同一个文件的同一位置
echo "分支B修改的内容" >> conflict.txt
git add .
git commit -m "分支B的修改"
```

### 步骤2：制造冲突

```bash
# 在 branch-b 上尝试合并 branch-a
git merge branch-a
```

> 你会看到冲突提示：
> ```
> Auto-merging conflict.txt
> CONFLICT (content): Merge conflict in conflict.txt
> Automatic merge failed; fix conflicts and then commit the result.
> ```

## 6.4 解决冲突

### 看看冲突标记

打开 `conflict.txt`，会看到这样的内容：

```
第一行内容
<<<<<<< HEAD
分支B修改的内容
=======
分支A修改的内容
>>>>>>> branch-a
```

- `<<<<<<< HEAD` — 当前分支（branch-b）的内容开始
- `=======` — 两个版本的分界线
- `>>>>>>> branch-a` — 被合并分支（branch-a）的内容结束

### 解决冲突的三种方式

1. **保留当前分支的版本**：删掉标记和 branch-a 的内容
2. **保留被合并分支的版本**：删掉标记和 branch-b 的内容
3. **两者都保留**：手动调整成你想要的最终版本

我们来用方式3：

```bash
# 编辑 conflict.txt，改成：
# 第一行内容
# 分支A修改的内容
# 分支B修改的内容
```

或者说：

```bash
# 快速操作：直接把整个冲突区域替换为两行都保留
echo "第一行内容" > conflict.txt
echo "分支A修改的内容" >> conflict.txt
echo "分支B修改的内容" >> conflict.txt
```

### 完成合并

```bash
# 标记冲突已解决
git add conflict.txt

# 完成合并提交
git commit -m "解决冲突：合并 branch-a 和 branch-b 的修改"

# 分支合并完毕
```

## 6.5 解决冲突的最佳实践

- 使用带图形界面的工具会更直观：`git mergetool`
- VS Code 内置了冲突解决工具（打开冲突文件就能看到图形化按钮）
- 如果不确定该保留什么，**和同事沟通**后再决定
- 解决冲突后**一定要测试**代码是否能正常运行

## ✅ 今日练习

1. 按照 6.3 节的步骤，在本地制造一个冲突
2. 打开冲突文件，观察冲突标记 `<` `=` `>`
3. 解决冲突（两种修改都保留）
4. 提交合并完成
5. 运行 `git log --oneline --graph` 看分支合并的图形化历史

---

**完成了吗？进入 [第7课](./lesson-07.md)，学习 Pull Request 工作流！**
