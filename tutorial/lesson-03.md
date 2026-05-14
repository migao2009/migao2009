# 第3课：查看历史与撤销修改

**预计时间：30分钟**

> **上节课回顾**：你学会了 `git init`、`git add`、`git commit`。
>
> **本节课目标**：查看提交历史、查看文件差异、撤销修改。

## 3.1 查看提交历史

### git log — 查看所有提交

```bash
git log
```

> **👀 观察输出**：你会看到类似这样的信息：
> ```
> commit a1b2c3d4... (HEAD -> main)
> Author: 你的名字 <你的邮箱>
> Date:   ...
>
>     在 hello.txt 中添加第二行
> 
> commit e5f6g7h8...
> Author: 你的名字 <你的邮箱>
> Date:   ...
>
>     第一次提交：添加 hello.txt
> ```

每一行都是：
- **commit ID**：一串长长的字符（`a1b2c3d4...`），每次提交的唯一身份证
- **Author**：谁做的提交
- **Date**：提交时间
- **Message**：提交信息

### 让日志更好看

```bash
# 一行显示一条记录
git log --oneline

# 显示最近 2 条
git log -2

# 图形化显示（后面学到分支时会很有用）
git log --oneline --graph --all
```

## 3.2 查看文件差异

### git diff — 看看改了哪些内容

先修改文件，然后用 `git diff` 查看修改了什么：

```bash
# 在 hello.txt 中添加一行
echo "Third line!" >> hello.txt

# 查看修改内容（比一比工作区和暂存区的区别）
git diff
```

> **👀 观察输出**：
> - 绿色开头的行（`+`）表示新增的内容
> - 红色开头的行（`-`）表示删除的内容
> - 这就是标准的"diff"格式

### 不同阶段的 diff

```bash
# 工作区 vs 暂存区（还没 git add）
git diff

# 暂存区 vs 最近一次提交（已经 git add 了）
git diff --staged

# 查看两个提交之间的差异
git diff <commit1> <commit2>
```

## 3.3 撤销修改

### 情况1：还没 git add（在工作区）

```bash
# 撤销对文件的修改，回到最近一次提交的状态
git checkout -- hello.txt

# 或者用新版命令（推荐）：
git restore hello.txt
```

### 情况2：已经 git add（在暂存区）

```bash
# 从暂存区移除，但保留在工作区
git restore --staged hello.txt

# 也可以这样（老版本命令）：
git reset HEAD hello.txt
```

### 情况3：已经 git commit

> ⚠️ **注意**：如果已经 push 到 GitHub，**不要**使用下面这种方法撤销！只适用于本地提交。

```bash
# 撤销最近一次提交，但保留修改在工作区
git reset --soft HEAD~1

# 完全撤销最近一次提交，删除所有修改（谨慎！）
git reset --hard HEAD~1
```

> `HEAD` 表示当前最新的提交，`HEAD~1` 表示前一个提交。

## 3.4 实操练习

让我们完整走一遍撤销流程：

```bash
# 1. 创建一个测试文件
echo "这是测试内容" > test.txt

# 2. 添加并提交
git add test.txt
git commit -m "添加临时测试文件"

# 3. 再次修改
echo "更多内容" >> test.txt

# 4. 查看差异
git diff

# 5. 撤销修改（还没 add）
git restore test.txt

# 6. 确认文件恢复了
cat test.txt

# 7. 可以安全删除这个测试文件了
rm test.txt
git add .
git commit -m "删除测试文件"
```

## ✅ 今日练习

1. 运行 `git log --oneline` 查看当前仓库的提交历史
2. 修改 `favorite.txt`（上一课创建的），加几行新内容
3. 用 `git diff` 查看修改了什么
4. 用 `git restore favorite.txt` 撤销修改，确认文件回到原来状态
5. 再次修改并提交，这次用 `git log -1` 确认提交成功

---

**完成了吗？进入 [第4课](./lesson-04.md)，开始连接 GitHub！**
