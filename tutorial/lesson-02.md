# 第2课：你的第一次提交

**预计时间：30分钟**

> **上节课回顾**：你安装了 Git 并配置了用户名和邮箱。
>
> **本节课目标**：初始化仓库 → 创建文件 → 提交到 Git。

## 2.1 工作流程概览

```
工作区（你编辑的文件） → 暂存区（git add） → 仓库（git commit）
```

就像是：
1. 你写了一些代码（工作区）
2. 告诉 Git 哪些文件要保存（`git add` → 放到暂存区）
3. 正式拍照存档（`git commit` → 存入仓库）

## 2.2 初始化仓库

首先，我们需要告诉 Git："从这个文件夹开始进行版本管理"。

> **👉 动手操作：**

```bash
# 确保你在本教程的仓库目录下
cd e:\vsgithub\migao2009

# 初始化 Git 仓库（如果还没有）
git init
```

如果显示 `Initialized empty Git repository`，说明成功！  
（这个仓库已经初始化过了，所以可能提示 `Reinitialized`，也没问题）

## 2.3 查看仓库状态

这是你以后**最常用**的命令：

```bash
git status
```

> **👀 观察输出**：它会告诉你当前在哪个分支（`On branch main`），以及有没有未提交的修改。

## 2.4 创建文件并提交

让我们创建一个新文件，然后提交到 Git：

```bash
# 创建一个 hello.txt 文件
echo "Hello, Git!" > hello.txt

# 查看状态
git status
```

> **👀 观察输出**：你应该看到 `hello.txt` 显示在 **Untracked files**（未跟踪的文件）下面。意思是 Git 注意到这个文件了，但还没有开始管理它。

### 第一步：git add（放到暂存区）

```bash
# 把 hello.txt 加入暂存区
git add hello.txt

# 再次查看状态
git status
```

> **👀 观察输出**：现在 `hello.txt` 出现在 **Changes to be committed**（待提交的修改）下面了。

### 第二步：git commit（正式提交）

```bash
git commit -m "第一次提交：添加 hello.txt"
```

> **👀 观察输出**：你会看到类似这样的信息：
> ```
> 1 file changed, 1 insertion(+)
> create mode 100644 hello.txt
> ```

**恭喜！你完成了第一次 Git 提交！🎉**

## 2.5 再次修改并提交

让我们修改文件，再提交一次，感受一下流程：

```bash
# 追加一行内容到 hello.txt
echo "My second line!" >> hello.txt

# 查看状态（会看到 hello.txt 被修改了）
git status

# 添加到暂存区
git add hello.txt

# 提交
git commit -m "在 hello.txt 中添加第二行"
```

## 2.6 小贴士：写好的提交信息

提交信息（`-m` 后面的内容）是写给未来自己看的。好的提交信息：

- ✅ `修复登录按钮点击无反应的问题`
- ✅ `添加用户注册功能`
- ❌ `fix`（太模糊）
- ❌ `修改了一些东西`（等于没写）

> **黄金法则**：好的提交信息应该能回答"这个提交做了什么？"

## 2.7 git add 的快捷方式

如果你修改了多个文件，想一次性全部加入暂存区：

```bash
# 添加所有文件（谨慎使用，注意检查）
git add .
```

> ⚠️ 初学时建议每次 `git add 文件名`，明确知道自己添加了哪些文件。

## ✅ 今日练习

1. 创建一个新文件 `favorite.txt`，里面写上一句你喜欢的话
2. 执行 `git status` 观察变化
3. 执行 `git add favorite.txt`
4. 执行 `git commit -m "添加 favorite.txt"` 完成提交

---

**完成了吗？提交成功的话，进入 [第3课](./lesson-03.md) 学习如何查看历史！**
