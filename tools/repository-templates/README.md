# 十个独立仓库的管理与验证模板

该工具生成可移入十个真实仓库的本地文件，不创建 Git、远端、账号或部署。
输入来自设计仓的现有模块契约、交付计划、原范围追踪和记录注册表；引用保留原 ID、Owner 与验收责任，模板不是第二套任务板。

```sh
python3 ecosystem-repository-templates/generate.py \
  --source-root /absolute/path/to/soulidity \
  --output /absolute/path/to/empty/repositories
python3 /absolute/path/to/empty/repositories/soul-sdk/scripts/ci.py
python3 ecosystem-repository-templates/verify_generated.py \
  /absolute/path/to/empty/repositories
python3 ecosystem-repository-templates/test_templates.py \
  --source-root /absolute/path/to/soulidity
```

输出目录必须不存在或为空；重复运行会拒绝覆盖。可用 `--module SDK` 单独生成一个模块。
生成清单记录源文件摘要、每仓文件摘要和生成器身份，便于核对迁入的是同一批文件。

每仓包含 README、MODULE、AGENTS、COMPATIBILITY、RUNBOOK 和本地/远端 CI 六类产物。
`module.json` 保存十字段 Agent 合同、两项责任映射、四类工程权限适用性、八阶段退出条件、七类依赖和八项消费者声明。
未落实的实际责任人、ABI、依赖版本、发布单元和运行证明均保持 pending。
角色建议不任命实际人员；源码维护、版本发布、生产部署、链上控制分别登记，升级权不等于运行权。

`scripts/ci.py` 默认只验证维护契约和引用结构；其通过不能证明产品构建、独立升级或用户旅程通过。
迁入真实源码后，在 `ci.product_commands` 登记本仓可运行命令，再执行 `--product`。
命令使用参数数组、不经过 shell；执行范围为当前仓库。具体进程依然需要工作树/容器及工具权限隔离，路径检查不是操作系统沙箱。

产品命令记录形如 `{"id":"unit","argv":["python3","tests/check.py"],"timeout_seconds":120}`。
`release_units` 每项至少记录 `id/kind/exact_version/source_identity/artifact_identity/upgrade_boundary`，准确边界以实际包及权限路径为准。
发布证据每项使用 `{"path":"evidence/build.json","sha256":"实际64位摘要"}`；准备检查校验仓内文件和摘要，不凭远程链接声称通过。
改变生成内容后按真实任务继续维护；`verify_generated.py` 只用于核对迁入前的原批次，不是永久禁止后续源码变化。

九仓生成手动版本发布准备检查，Integration 生成手动组合准备检查；合计十 CI＋九发布准备＋一组合检查。
`--release-ready` 会拒绝未完成的真实验收材料。工作流只检查准备材料，不发布制品、部署或签名。
GitHub 上启用与实际运行仍需真实仓库的运行证据，生成器不会把模板写为已启用。

推进时在原 Delivery/DEV/BUG 追加 stage、status、evidence、exit criteria 和手册适用记录。
`delivery_attachment` 是原卡附件的结构，不维护本地 backlog；历史原记录状态不会被复制成当前阶段或完成状态。
跨仓缺陷由原卡交接对应维护者，不顺手修改其他仓库。
