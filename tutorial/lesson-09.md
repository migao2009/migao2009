# 第9课：实战项目

**预计时间：60分钟**

> **上节课回顾**：你学会了 .gitignore 和提交规范。
>
> **本节课目标**：通过一个小项目，完整走一遍 Git/GitHub 工作流。

## 9.1 项目简介

我们将创建一个 **"我的学习笔记"** 项目——一个用 Markdown 写的小型知识库。

```
my-notes/
├── README.md          # 项目介绍
├── .gitignore         # 忽略文件
├── notes/             # 笔记目录
│   ├── git-笔记.md
│   └── html-笔记.md
└── index.md           # 笔记索引页
```

## 9.2 开始项目

### 步骤1：创建项目结构

```bash
# 回到仓库根目录
cd e:\vsgithub\migao2009

# 创建目录
mkdir -p notes
```

### 步骤2：创建 README.md

```bash
cat > README.md << 'EOF'
# 我的学习笔记

这是我学习 Git/GitHub 的笔记仓库。

## 笔记列表

- [Git 笔记](notes/git-笔记.md)
- [HTML 笔记](notes/html-笔记.md)

## 关于

使用 Markdown 编写。
EOF
```

### 步骤3：创建 Git 笔记

```bash
cat > notes/git-笔记.md << 'EOF'
# Git 学习笔记

## 基本命令

- `git init`：初始化仓库
- `git add <文件>`：添加文件到暂存区
- `git commit -m "信息"`：提交
- `git status`：查看状态
- `git log`：查看历史

## 分支操作

- `git branch`：查看分支
- `git checkout -b <分支名>`：创建并切换分支
- `git merge <分支名>`：合并分支

## 远程操作

- `git push`：推送到远程
- `git pull`：拉取远程更新
- `git clone <地址>`：克隆仓库
EOF
```

### 步骤4：创建 HTML 笔记

```bash
cat > notes/html-笔记.md << 'EOF'
# HTML 学习笔记

## 基本结构

```html
<!DOCTYPE html>
<html>
<head>
    <title>页面标题</title>
</head>
<body>
    <h1>标题</h1>
    <p>段落</p>
</body>
</html>
```

## 常用标签

- `<h1>` ~ `<h6>`：标题
- `<p>`：段落
- `<a>`：链接
- `<img>`：图片
- `<ul>` / `<ol>`：列表
EOF
```

### 步骤5：创建 index.md

```bash
cat > index.md << 'EOF'
# 目录

欢迎来到我的学习笔记！

- [Git 笔记](notes/git-笔记.md)
- [HTML 笔记](notes/html-笔记.md)

---

最后更新时间：2026年5月
EOF
```

### 步骤6：创建 .gitignore

```bash
echo "*.log" > .gitignore
echo "temp/" >> .gitignore
```

## 9.3 使用 Git 管理项目

### 全部提交

```bash
# 查看状态
git status

# 逐个添加（推荐）
git add .gitignore
git add README.md
git add notes/git-笔记.md
git add notes/html-笔记.md
git add index.md

# 也可以批量
git add .

# 提交
git commit -m "feat: 创建学习笔记项目

- 添加 Git 和 HTML 学习笔记
- 创建笔记索引页
- 配置 .gitignore"
```

## 9.4 推送到 GitHub

```bash
# 如果还没关联远程仓库
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 推送
git push -u origin main
```

## 9.5 用 PR 工作流添加新功能

### 创建一个新功能分支

```bash
git checkout -b feature/添加CSS笔记
```

### 添加 CSS 笔记

```bash
cat > notes/css-笔记.md << 'EOF'
# CSS 学习笔记

## 基本语法

```css
选择器 {
    属性: 值;
}
```

## 常见属性

- `color`：文字颜色
- `font-size`：字号
- `margin`：外边距
- `padding`：内边距
EOF
```

### 更新索引

```bash
cat >> index.md << 'EOF'

- [CSS 笔记](notes/css-笔记.md)
EOF
```

### 提交并推送

```bash
git add notes/css-笔记.md index.md
git commit -m "feat: 添加 CSS 学习笔记"
git push -u origin feature/添加CSS笔记
```

### 创建 Pull Request

1. 打开 GitHub
2. 你会看到提示创建 PR → 点击
3. 填写标题和描述
4. 合并 PR

### 本地同步

```bash
git checkout main
git pull
git branch -d feature/添加CSS笔记
```

## ✅ 今日练习

1. 按教程步骤创建"我的学习笔记"项目
2. 全部提交到 main 分支
3. 推送到 GitHub
4. 创建新分支添加一篇你感兴趣的笔记（JavaScript、Python 等等）
5. 在 GitHub 上创建 PR 并合并
6. 本地同步

---

**太棒了！你已经完成了一个完整的 Git/GitHub 工作流！🎉 进入 [第10课](./lesson-10.md)，学习一些常用技巧。**
