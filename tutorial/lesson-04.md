# 第4课：连接 GitHub

**预计时间：45分钟**

> **上节课回顾**：你学会了查看提交历史 (`git log`) 和撤销修改。
>
> **本节课目标**：注册 GitHub → 创建远程仓库 → 把本地代码推送到 GitHub。

## 4.1 注册 GitHub 账号

1. 打开 https://github.com
2. 点击 **Sign up**
3. 输入用户名、邮箱、密码
4. 验证邮箱
5. 完成！🎉

## 4.2 在 GitHub 上创建仓库

1. 登录 GitHub 后，点击右上角 **+** → **New repository**
2. 填写仓库名（例如 `my-first-repo`）
3. 选择 **Public**（公开）或 **Private**（私有，自己可见）
4. **不要勾选** "Add a README file"（因为我们已经有了）
5. 点击 **Create repository**

创建完成后会跳转到一个页面，上面显示了几种推送方式。

## 4.3 关联本地仓库和 GitHub 仓库

在 GitHub 创建好仓库后，你会看到一个快速设置页面。找到**第二块**内容：

```bash
git remote add origin https://github.com/你的用户名/my-first-repo.git
```

> **解释一下**：
> - `remote`：远程仓库
> - `add`：添加
> - `origin`：远程仓库的名字（约定俗成叫 origin）
> - 后面的 URL：你的 GitHub 仓库地址

### 实操

把这个仓库连接到 GitHub：

```bash
# 先看当前有没有关联远程仓库
git remote -v
```

如果什么都没有，就添加：

```bash
git remote add origin https://github.com/你的用户名/my-first-repo.git
```

> 把命令中的 URL 换成你仓库实际的地址！

## 4.4 推送到 GitHub

```bash
git push -u origin main
```

- `push`：推送
- `-u`：建立 upstream 关联（以后就可以直接用 `git push`）
- `origin`：远程仓库名
- `main`：分支名

> 第一次 push 可能会弹出 GitHub 的登录窗口，按照提示登录授权即可。

完成后，刷新 GitHub 页面，你会看到代码已经上传了！🎉

## 4.5 从 GitHub 拉取代码

### git clone — 克隆仓库到本地

```bash
# 把 GitHub 上的仓库下载到本地
git clone https://github.com/别人的用户名/别人的仓库.git
```

### git pull — 拉取远程更新

```bash
# 如果队友推送了新代码，你可以拉取到本地
git pull
```

## 4.6 完整工作流（本地 ↔ GitHub）

```
本地修改 → git add → git commit → git push (到 GitHub)
                                           ↓
                            其他人在 GitHub 上看到更新
                                           ↓
                            其他人用 git pull 下载到本地
```

### 常用操作组合

```bash
# 一天工作的标准流程
git status          # 1. 看看当前状态
git add .           # 2. 添加所有修改
git commit -m "xxx" # 3. 提交
git push            # 4. 推送到 GitHub
```

## ✅ 今日练习

1. 注册 GitHub 账号（如果还没有）
2. 在 GitHub 上创建一个新的仓库
3. 用 `git remote add origin <你的仓库地址>` 关联远程仓库
4. 用 `git push -u origin main` 推送代码
5. 刷新 GitHub 页面，确认代码已上传
6. 修改本地的 `README.md`，提交后再次 `git push`，观察 GitHub 上内容的变化

---

**完成了吗？进入 [第5课](./lesson-05.md)，学习分支操作！**
