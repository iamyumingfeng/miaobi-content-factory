# ========================================
# AIGC平台 - Makefile
# ========================================

.PHONY: help
.PHONY: dev-deploy-docker dev-status dev-logs dev-stop dev-restart
.PHONY: prod-deploy prod-upgrade prod-rollback prod-backup prod-status prod-logs

.DEFAULT_GOAL := help

# 颜色输出
COLOR_RESET = \033[0m
COLOR_INFO = \033[36m
COLOR_SUCCESS = \033[32m
COLOR_WARNING = \033[33m
COLOR_ERROR = \033[31m

# ========================================
# 帮助
# ========================================
help: ## 显示帮助
	@echo "$(COLOR_INFO)【开发环境部署】$(COLOR_RESET)"
	@grep -E '^dev-[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_SUCCESS)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(COLOR_INFO)【生产环境部署】$(COLOR_RESET)"
	@grep -E '^prod-[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_SUCCESS)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(COLOR_INFO)【更多信息】$(COLOR_RESET)"
	@echo "  开发环境调试脚本: docs/dev-debug-guide.md"
	@echo "  开发环境部署文档: docs/dev-deploy-guide.md"
	@echo "  生产环境部署文档: docs/prod-deploy-guide.md"
	@echo ""

# ========================================
# 开发环境部署
# ========================================
dev-deploy-docker: ## 开发环境 Docker 部署（推荐）
	@echo "$(COLOR_INFO)开发环境 Docker 部署...$(COLOR_RESET)"
	@chmod +x scripts/*.sh
	@./scripts/dev-deploy.sh docker

dev-status: ## 查看开发环境服务状态
	@chmod +x scripts/*.sh
	@./scripts/dev-deploy.sh status

dev-logs: ## 查看开发环境服务日志
	@chmod +x scripts/*.sh
	@./scripts/dev-deploy.sh logs

dev-stop: ## 停止开发环境服务
	@chmod +x scripts/*.sh
	@./scripts/dev-deploy.sh stop

dev-restart: ## 重启开发环境服务
	@chmod +x scripts/*.sh
	@./scripts/dev-deploy.sh restart

# ========================================
# 生产环境部署
# ========================================
prod-deploy: ## 生产环境首次部署
	@echo "$(COLOR_INFO)生产环境首次部署...$(COLOR_RESET)"
	@chmod +x scripts/*.sh
	@./scripts/prod-deploy.sh deploy

prod-upgrade: ## 生产环境升级部署
	@echo "$(COLOR_INFO)生产环境升级部署...$(COLOR_RESET)"
	@chmod +x scripts/*.sh
	@./scripts/prod-deploy.sh upgrade

prod-rollback: ## 回滚到上一版本
	@echo "$(COLOR_INFO)回滚到上一版本...$(COLOR_RESET)"
	@chmod +x scripts/*.sh
	@./scripts/prod-deploy.sh rollback

prod-backup: ## 手动备份数据
	@echo "$(COLOR_INFO)手动备份数据...$(COLOR_RESET)"
	@chmod +x scripts/*.sh
	@./scripts/prod-deploy.sh backup

prod-status: ## 查看生产服务状态
	@chmod +x scripts/*.sh
	@./scripts/prod-deploy.sh status

prod-logs: ## 查看生产服务日志
	@chmod +x scripts/*.sh
	@./scripts/prod-deploy.sh logs