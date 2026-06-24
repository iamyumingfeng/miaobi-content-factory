<template>
  <div class="template-list-view">
    <h2 class="page-title">模板创作库</h2>

    <el-row :gutter="20">
      <el-col :span="5">
        <div class="card category-panel">
          <!-- 超级管理员：管理员筛选 -->
          <div v-if="isSuperAdmin" class="admin-filter mb-md">
            <el-select
              v-model="selectedAdminId"
              placeholder="筛选管理员"
              style="width: 100%;"
              @change="handleAdminChange"
            >
              <el-option label="全部" value="" />
              <el-option
                v-for="operator in operators"
                :key="operator.id"
                :label="operator.nickname || operator.userid"
                :value="operator.id"
              />
            </el-select>
          </div>
          <!-- 3级分类标签树 -->
          <div class="panel-header flex-between">
            <span class="panel-title">素材列表</span>
            <el-button v-if="!isSuperAdmin" type="primary" :icon="Plus" size="small" @click="handleAddPlatform">
              添加
            </el-button>
          </div>
          <el-tree
            :data="categoryTree"
            :props="categoryTreeProps"
            node-key="key"
            default-expand-all
            highlight-current
            :expand-on-click-node="false"
            @node-click="handleNodeClick"
          >
            <template #default="{ node, data }">
              <span class="custom-tree-node">
                <span class="node-label">
                  <el-icon v-if="data.type === 'platform'" :style="{ color: data.color || '#8B7CF6' }">
                    <Folder />
                  </el-icon>
                  <el-icon v-else-if="data.type === 'category'" :style="{ color: data.color || '#67C23A' }">
                    <Tickets />
                  </el-icon>
                  <el-icon v-else-if="data.type === 'tag' || data.type === 'no_tag'" :style="{ color: data.color || '#909399' }">
                    <PriceTag />
                  </el-icon>
                  <span class="label-text">{{ node.label }}</span>
                  <span v-if="data.isSystem" class="system-badge">系统</span>
                  <span v-if="data.count !== undefined" class="count-badge">{{ data.count }}</span>
                </span>
                <span v-if="data.type === 'platform'" class="node-actions">
                  <el-icon class="action-icon add" @click.stop="handleAddCategory(data)" title="添加分类">
                    <Plus />
                  </el-icon>
                  <el-icon class="action-icon delete" @click.stop="handleDeletePlatform(data)" title="删除平台">
                    <Delete />
                  </el-icon>
                </span>
                <span v-else-if="data.type === 'category' && !data.isSystem" class="node-actions">
                  <el-icon class="action-icon add" @click.stop="handleAddTag(data)" title="添加标签">
                    <Plus />
                  </el-icon>
                  <el-icon class="action-icon delete" @click.stop="handleRemoveCategory(data)" title="删除分类">
                    <Delete />
                  </el-icon>
                </span>
                <span v-else-if="data.type === 'tag' && !data.isSystem" class="node-actions">
                  <el-icon class="action-icon delete" @click.stop="handleRemoveTag(data)" title="删除标签">
                    <Delete />
                  </el-icon>
                </span>
              </span>
            </template>
          </el-tree>
        </div>
      </el-col>

      <el-col :span="19">
        <div class="card">
          <div class="toolbar flex-between mb-md">
            <div class="toolbar-left flex gap-md">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索素材创作名称"
                :prefix-icon="Search"
                clearable
                style="width: 240px;"
              />
              <el-select v-model="searchContentType" placeholder="内容类型" clearable style="width: 120px;">
                <el-option label="全部" value="" />
                <el-option label="纯文本" value="text" />
                <el-option label="图文" value="image_text" />
                <el-option label="视频" value="video_text" />
              </el-select>
              <el-select v-model="searchStatus" placeholder="状态筛选" clearable style="width: 120px;">
                <el-option label="全部" value="" />
                <el-option label="已启用" value="enabled" />
                <el-option label="已禁用" value="disabled" />
              </el-select>
              <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
            </div>
            <div class="toolbar-right">
              <el-button v-if="!isSuperAdmin" type="primary" :icon="Plus" @click="showCreateDialog = true">上传素材</el-button>
            </div>
          </div>

          <el-tabs v-model="viewMode" class="view-tabs">
            <el-tab-pane label="卡片视图" name="card">
              <div v-if="loading" class="loading-container">
                <el-icon class="is-loading" :size="32"><Loading /></el-icon>
                <span>加载中...</span>
              </div>
              <div v-else-if="templateList.length === 0" class="empty-container">
                <el-empty description="暂无素材创作数据" />
              </div>
              <div v-else class="template-grid">
                <el-card
                  v-for="template in templateList"
                  :key="template.id"
                  class="template-card"
                  shadow="hover"
                >
                  <template #header>
                    <div class="card-header flex-between">
                      <span class="template-name">{{ template.name }}</span>
                      <div class="header-tags">
                        <el-tag :type="template.status === 'enabled' ? 'success' : 'info'" size="small">
                          {{ template.status === 'enabled' ? '已启用' : '已禁用' }}
                        </el-tag>
                      </div>
                    </div>
                  </template>
                  <div class="template-preview">
                    <div v-if="template.content_type === 'text' || !template.content_type || template.content_type === 'video_text'" class="text-preview">
                      <el-icon :size="48" color="#909399"><Document /></el-icon>
                      <div class="text-snippet">{{ getTextSnippet(template.prompt_template) }}</div>
                    </div>
                    <div v-else class="image-preview-wrapper" @click="handlePreviewImage(template)">
                      <el-image
                        :src="getTemplateThumbnail(template)"
                        fit="cover"
                        class="preview-image"
                      >
                        <template #error>
                          <div class="image-placeholder">
                            <el-icon :size="32" color="#909399"><Picture /></el-icon>
                          </div>
                        </template>
                      </el-image>
                      <div v-if="getTemplateImageCount(template) > 1" class="image-count-badge">
                        <el-icon><Picture /></el-icon>
                        <span>{{ getTemplateImageCount(template) }}</span>
                      </div>
                      <div class="image-hover-overlay">
                        <el-icon :size="24"><View /></el-icon>
                        <span>点击查看</span>
                      </div>
                    </div>
                  </div>
                  <div class="template-info">
                    <div class="info-row">
                      <span class="label">分类:</span>
                      <span class="value">{{ template.category?.name || '未分类' }}</span>
                    </div>
                    <div class="info-row">
                      <span class="label">标签:</span>
                      <span class="value">
                        <template v-if="template.tags && template.tags.length > 0">
                          <el-tag v-for="tag in template.tags" :key="tag.id" size="small" type="info" class="mr-xs">{{ tag.name }}</el-tag>
                        </template>
                        <template v-else>无标签</template>
                      </span>
                    </div>
                    <div class="info-row">
                      <span class="label">类型:</span>
                      <el-tag size="small" type="info">{{ getContentTypeLabel(template.content_type) }}</el-tag>
                    </div>
                    <div v-if="isSuperAdmin" class="info-row">
                      <span class="label">所属管理:</span>
                      <span class="value">{{ template.owner_admin_id ? getAdminName(template.owner_admin_id) : '无' }}</span>
                    </div>
                    <div class="info-row">
                      <span class="label">创建时间:</span>
                      <span class="value">{{ formatDate(template.created_at) }}</span>
                    </div>
                    <!-- 产品名称 -->
                    <div class="info-row" v-if="template.product_name">
                      <span class="label">产品名称:</span>
                      <span class="value">{{ template.product_name }}</span>
                    </div>
                    <!-- 产品卖点 -->
                    <div class="info-row" v-if="template.product_selling_points">
                      <span class="label">产品卖点:</span>
                      <span class="value selling-points">{{ template.product_selling_points }}</span>
                    </div>
                    <!-- 爆款类型 -->
                    <div class="info-row" v-if="template.viral_type">
                      <span class="label">爆款类型:</span>
                      <span class="value">
                        <el-tag size="small" type="warning">{{ getViralTypeLabel(template.viral_type) }}</el-tag>
                      </span>
                    </div>
                    <!-- 创意种子 -->
                    <div class="info-row" v-if="template.opening_seed_id || template.emotion_seed_id || template.ending_seed_id">
                      <span class="label">创意种子:</span>
                      <span class="value seed-tags">
                        <el-tag size="small" type="primary" v-if="getSeedName(template.opening_seed_id, 'opening')" class="mr-xs">
                          开头: {{ getSeedName(template.opening_seed_id, 'opening') }}
                        </el-tag>
                        <el-tag size="small" type="primary" v-if="getSeedName(template.emotion_seed_id, 'emotion')" class="mr-xs">
                          情感: {{ getSeedName(template.emotion_seed_id, 'emotion') }}
                        </el-tag>
                        <el-tag size="small" type="primary" v-if="getSeedName(template.ending_seed_id, 'ending')" class="mr-xs">
                          结尾: {{ getSeedName(template.ending_seed_id, 'ending') }}
                        </el-tag>
                      </span>
                    </div>
                  </div>
                  <div class="template-actions">
                    <el-button type="primary" link size="small" @click="handleEdit(template)">编辑</el-button>
                    <el-button type="info" link size="small" @click="handleViewDetail(template)">详情</el-button>
                    <el-button type="success" link size="small" @click="handleCopy(template)">复制</el-button>
                    <el-button :type="template.status === 'enabled' ? 'warning' : 'success'" link size="small" @click="handleToggleStatus(template)">
                      {{ template.status === 'enabled' ? '禁用' : '启用' }}
                    </el-button>
                    <el-button type="danger" link size="small" @click="handleDelete(template)">删除</el-button>
                  </div>
                </el-card>
              </div>
            </el-tab-pane>

            <el-tab-pane label="列表视图" name="list">
              <div v-if="loading" class="loading-container">
                <el-icon class="is-loading" :size="32"><Loading /></el-icon>
                <span>加载中...</span>
              </div>
              <template v-else>
                <div class="list-toolbar mb-md">
                  <span class="selected-count" v-if="selectedIds.length > 0">已选 {{ selectedIds.length }} 项</span>
                  <template v-if="selectedIds.length > 0">
                    <el-button type="success" size="small" @click="handleBatchEnable">批量启用</el-button>
                    <el-button type="warning" size="small" @click="handleBatchDisable">批量禁用</el-button>
                    <el-button type="primary" size="small" @click="handleBatchCopy">批量复制</el-button>
                    <el-button type="warning" size="small" @click="handleBatchMigrate">批量迁移</el-button>
                    <el-button type="danger" size="small" @click="handleBatchDelete">批量删除</el-button>
                  </template>
                </div>
                <el-table :data="templateList" style="width: 100%" @selection-change="handleSelectionChange">
                  <el-table-column type="selection" width="55" />
                  <el-table-column label="预览" width="120">
                    <template #default="{ row }">
                      <div
                        v-if="row.content_type === 'image_text'"
                        class="list-image-wrapper"
                        @click="handlePreviewImage(row)"
                      >
                        <el-image
                          :src="getTemplateThumbnail(row)"
                          fit="cover"
                          style="width: 80px; height: 60px; border-radius: 4px;"
                        />
                        <div v-if="getTemplateImageCount(row) > 1" class="list-image-count">
                          {{ getTemplateImageCount(row) }}
                        </div>
                      </div>
                      <el-icon v-else :size="32" color="#909399"><Document /></el-icon>
                    </template>
                  </el-table-column>
                  <el-table-column prop="name" label="素材创作名称" min-width="180" />
                  <el-table-column v-if="isSuperAdmin" label="所属管理者" width="100">
                    <template #default="{ row }">
                      <template v-if="row.owner_admin_id">{{ getAdminName(row.owner_admin_id) }}
                    </template>
                      <template v-else>
                        无
                      </template>
                    </template>
                  </el-table-column>
                  <el-table-column label="分类" width="100">
                    <template #default="{ row }">
                      {{ row.category?.name || '未分类' }}
                    </template>
                  </el-table-column>
                  <el-table-column label="标签" width="180">
                    <template #default="{ row }">
                      <template v-if="row.tags && row.tags.length > 0">
                        <el-tag v-for="tag in row.tags" :key="tag.id" size="small" type="info" class="mr-xs">{{ tag.name }}</el-tag>
                      </template>
                      <template v-else>无标签</template>
                    </template>
                  </el-table-column>
                  <el-table-column label="类型" width="100">
                    <template #default="{ row }">
                      <el-tag size="small" type="info">{{ getContentTypeLabel(row.content_type) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="status" label="状态" width="90">
                    <template #default="{ row }">
                      <el-tag :type="row.status === 'enabled' ? 'success' : 'info'" size="small">
                        {{ row.status === 'enabled' ? '已启用' : '已禁用' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="创建时间" width="170">
                    <template #default="{ row }">
                      {{ formatDate(row.created_at) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" min-width="220" fixed="right">
                    <template #default="{ row }">
                      <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
                      <el-button type="info" link size="small" @click="handleViewDetail(row)">详情</el-button>
                      <el-button :type="row.status === 'enabled' ? 'warning' : 'success'" link size="small" @click="handleToggleStatus(row)">
                        {{ row.status === 'enabled' ? '禁用' : '启用' }}
                      </el-button>
                      <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </template>
            </el-tab-pane>
          </el-tabs>

          <div class="pagination mt-lg flex-between">
            <span class="total-text">共 {{ total }} 条记录</span>
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[12, 24, 48, 96]"
              :total="total"
              layout="total, sizes, prev, pager, next, jumper"
            />
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 添加平台弹窗 -->
    <el-dialog v-model="showPlatformDialog" title="添加平台分类" width="450px">
      <el-form :model="platformForm" label-width="100px">
        <el-form-item label="平台名称" required>
          <el-input v-model="platformForm.name" placeholder="请输入平台名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="platformForm.description" type="textarea" :rows="2" placeholder="请输入描述（可选）" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="platformForm.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPlatformDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSavePlatform" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加分类弹窗 -->
    <el-dialog v-model="showCategoryDialog" title="添加分类" width="450px">
      <el-form :model="categoryForm" label-width="100px">
        <el-form-item label="所属平台">
          <el-input :value="categoryTreeData.find(p => p.id === selectedPlatformId)?.name || '全部'" disabled />
        </el-form-item>
        <el-form-item label="分类名称" required>
          <el-input v-model="categoryForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="categoryForm.description" type="textarea" :rows="2" placeholder="请输入描述（可选）" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="categoryForm.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCategoryDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveCategory" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加标签弹窗 -->
    <el-dialog v-model="showTagDialog" title="添加标签" width="450px">
      <el-form :model="tagForm" label-width="100px">
        <el-form-item label="所属分类">
          <el-input :value="selectedCategory?.name || '全部'" disabled />
        </el-form-item>
        <el-form-item label="标签名称" required>
          <el-input v-model="tagForm.name" placeholder="请输入标签名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="tagForm.description" type="textarea" :rows="2" placeholder="请输入描述（可选）" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="tagForm.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTagDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveTag" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 删除确认弹窗 -->
    <el-dialog v-model="showDeleteDialog" title="确认删除" width="500px">
      <el-alert
        v-if="deletingItem"
        :title="`确定要删除${deletingItem.type === 'platform' ? '平台' : deletingItem.type === 'category' ? '分类' : '标签'}「${deletingItem.name}」吗？`"
        type="warning"
        :closable="false"
        class="mb-md"
      />
      <div v-if="deletingItem" class="delete-info">
        <p v-if="deletingItem.template_count !== undefined && deletingItem.template_count > 0" style="color: #F56C6C; font-weight: 500;">
          该{{ deletingItem.type === 'platform' ? '平台' : deletingItem.type === 'category' ? '分类' : '标签' }}下有 <strong>{{ deletingItem.template_count }}</strong> 个素材关联，请先迁移或删除所有素材
        </p>
        <p v-else style="color: #67C23A; font-weight: 500;">
          该{{ deletingItem.type === 'platform' ? '平台' : deletingItem.type === 'category' ? '分类' : '标签' }}下无素材，可以安全删除
        </p>
        <p v-if="deletingItem.type === 'category' && deletingItem.tagCount && deletingItem.tagCount > 0" style="color: #F56C6C;">
          该分类下有 <strong>{{ deletingItem.tagCount }}</strong> 个标签，请先删除所有标签
        </p>
      </div>
      <template #footer>
        <el-button @click="showDeleteDialog = false">取消</el-button>
        <el-button
          type="danger"
          @click="handleConfirmDelete"
          :disabled="(deletingItem?.template_count || 0) > 0 || (deletingItem?.type === 'category' && (deletingItem?.tagCount || 0) > 0)"
        >
          确认删除
        </el-button>
      </template>
    </el-dialog>

    <!-- 创建/编辑素材创作弹窗 -->
    <el-dialog v-model="showCreateDialog" :title="templateEditMode ? '编辑素材' : '新建素材'" width="700px">
      <el-form :model="templateForm" label-width="120px">
        <el-form-item label="素材创作名称" required>
          <el-input v-model="templateForm.name" placeholder="请输入素材创作标题" />
        </el-form-item>
        <el-form-item label="提示词创意" required>
          <el-input
            v-model="templateForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入文案提示词创意点"
          />
        </el-form-item>
        <el-form-item label="产品卖点">
          <el-input
            v-model="templateForm.productSellingPoints"
            type="textarea"
            :rows="3"
            placeholder="输入产品卖点，生成文案时会重点强调（可选）"
          />
        </el-form-item>
        <el-form-item label="产品名称" required>
          <el-input
            v-model="templateForm.productName"
            placeholder="输入产品名称，用于提示词中明确推广的产品（必填）"
          />
          <div class="form-tip">产品名称会出现在提示词中，明确告诉 AI 要推广的产品，防止与对标素材混淆</div>
        </el-form-item>
        <el-form-item label="内容类型">
          <el-radio-group v-model="templateForm.contentType">
            <el-radio value="text">纯文本</el-radio>
            <el-radio value="image_text">图文</el-radio>
          </el-radio-group>
        </el-form-item>
        <!-- 图文类型时显示图片上传 -->
        <el-form-item v-if="templateForm.contentType === 'image_text'" label="素材图片">
          <div class="image-upload-area">
            <div v-for="(img, index) in templateForm.images" :key="index" class="image-preview-item">
              <el-image :src="img.url" fit="cover" class="preview-img" />
              <el-icon class="remove-icon" @click="removeTemplateImage(index)"><Close /></el-icon>
            </div>
            <el-upload
              :show-file-list="false"
              :on-change="handleTemplateImageChange"
              accept="image/*"
              class="image-uploader"
              :auto-upload="false"
            >
              <div class="upload-placeholder">
                <el-icon><Plus /></el-icon>
                <span>添加图片</span>
              </div>
            </el-upload>
          </div>
          <div class="upload-tip">支持添加多张图片</div>
        </el-form-item>
        <!-- 图文类型时显示图片尺寸设置 -->
        <el-form-item v-if="templateForm.contentType === 'image_text'" label="图片尺寸比例">
          <el-radio-group v-model="templateForm.imageSizeRatio">
            <el-radio value="1:1">2048×2048 (1:1)</el-radio>
            <el-radio value="4:3">2304×1728 (4:3)</el-radio>
            <el-radio value="16:9">2560×1440 (16:9)</el-radio>
            <el-radio value="3:4">1728×2304 (3:4)</el-radio>
            <el-radio value="9:16">1440×2560 (9:16)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="templateForm.contentType === 'image_text'" label="图片水印">
          <el-switch v-model="templateForm.addWatermark" />
        </el-form-item>
        <el-form-item label="提示词指令" required>
          <el-input
            v-model="templateForm.promptTemplate"
            type="textarea"
            :rows="6"
            placeholder="请输入提示词精确指令"
          />
        </el-form-item>
        <el-form-item label="所属平台" required>
          <el-select v-model="templateForm.platformId" placeholder="请选择平台" clearable style="width: 100%;" @change="handlePlatformChange">
            <el-option
              v-for="platform in getFlatPlatforms()"
              :key="platform.id"
              :label="platform.name"
              :value="platform.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属分类" required>
          <el-select v-model="templateForm.categoryId" placeholder="请选择分类" style="width: 100%;" :disabled="!templateForm.platformId" @change="handleCategoryChange">
            <el-option
              v-for="category in availableCategories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属标签" required>
          <el-select v-model="templateForm.tagIds" multiple placeholder="请选择标签" style="width: 100%;">
            <el-option
              v-for="tag in availableTags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
        </el-form-item>
        <!-- ===== 爆款模板配置 ===== -->
        <el-divider content-position="left">爆款模板配置</el-divider>
        <el-form-item label="爆款类型">
          <el-select v-model="templateForm.viralType" placeholder="随机选择" clearable style="width: 100%;">
            <el-option label="随机选择" value="auto" />
            <el-option
              v-for="vt in viralTypeOptions"
              :key="vt.value"
              :label="vt.label"
              :value="vt.value"
            >
              <div class="viral-type-option">
                <span class="viral-type-label">{{ vt.label }}</span>
                <span class="viral-type-desc">{{ vt.description }}</span>
              </div>
            </el-option>
          </el-select>
          <div v-if="templateForm.viralType" class="viral-type-preview">
            {{ getViralTypeDescription(templateForm.viralType) }}
          </div>
        </el-form-item>
        <el-form-item label="开头模式">
          <el-select v-model="templateForm.openingSeedId" placeholder="随机选择" clearable style="width: 100%;">
            <el-option label="随机选择" value="auto" />
            <el-option
              v-for="seed in openingSeeds"
              :key="seed.id"
              :label="seed.name"
              :value="String(seed.id)"
            />
          </el-select>
          <div v-if="templateForm.openingSeedId && templateForm.openingSeedId !== 'auto'" class="seed-preview">
            {{ getSeedPreview(templateForm.openingSeedId, 'opening') }}
          </div>
        </el-form-item>
        <el-form-item label="情感基调">
          <el-select v-model="templateForm.emotionSeedId" placeholder="随机选择" clearable style="width: 100%;">
            <el-option label="随机选择" value="auto" />
            <el-option
              v-for="seed in emotionSeeds"
              :key="seed.id"
              :label="seed.name"
              :value="String(seed.id)"
            />
          </el-select>
          <div v-if="templateForm.emotionSeedId && templateForm.emotionSeedId !== 'auto'" class="seed-preview">
            {{ getSeedPreview(templateForm.emotionSeedId, 'emotion') }}
          </div>
        </el-form-item>
        <el-form-item label="结尾模式">
          <el-select v-model="templateForm.endingSeedId" placeholder="随机选择" clearable style="width: 100%;">
            <el-option label="随机选择" value="auto" />
            <el-option
              v-for="seed in endingSeeds"
              :key="seed.id"
              :label="seed.name"
              :value="String(seed.id)"
            />
          </el-select>
          <div v-if="templateForm.endingSeedId && templateForm.endingSeedId !== 'auto'" class="seed-preview">
            {{ getSeedPreview(templateForm.endingSeedId, 'ending') }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveTemplate" :loading="saving">{{ templateEditMode ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>

    <!-- 图片预览弹窗 -->
    <el-dialog
      v-model="showImagePreview"
      title="素材图片预览"
      width="800px"
      :close-on-click-modal="true"
      class="image-preview-dialog"
    >
      <div v-if="previewTemplate" class="image-preview-content">
        <div class="preview-template-title mb-md">{{ previewTemplate.name }}</div>
        <div class="preview-image-list">
          <div
            v-for="(imgUrl, index) in getTemplateImages(previewTemplate)"
            :key="index"
            class="preview-image-item"
          >
            <el-image
              :src="getFullImageUrl(imgUrl)"
              fit="contain"
              class="preview-full-image"
              :preview-src-list="getTemplateImages(previewTemplate).map(url => getFullImageUrl(url))"
              :initial-index="index"
            >
              <template #error>
                <div class="image-placeholder-large">
                  <el-icon :size="48" color="#909399"><Picture /></el-icon>
                  <span>图片加载失败</span>
                </div>
              </template>
            </el-image>
            <div class="preview-image-actions">
              <el-button size="small" type="primary" @click="downloadTemplateImage(imgUrl)">
                <el-icon><Download /></el-icon> 下载原图
              </el-button>
              <span class="image-index">{{ index + 1 }} / {{ getTemplateImages(previewTemplate).length }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 素材创作详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="素材创作详情" width="700px">
      <div v-if="detailTemplate" class="template-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="素材创作名称">{{ detailTemplate.name }}</el-descriptions-item>
          <el-descriptions-item label="内容类型">
            {{ getContentTypeLabel(detailTemplate.content_type) }}
          </el-descriptions-item>
          <el-descriptions-item label="所属平台" :span="2">
            {{ getTemplatePlatformName(detailTemplate) }}
          </el-descriptions-item>
          <el-descriptions-item label="所属分类" :span="2">
            {{ detailTemplate.category?.name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <template v-if="detailTemplate.tags && detailTemplate.tags.length > 0">
              <el-tag v-for="tag in detailTemplate.tags" :key="tag.id" size="small" type="info" class="mr-xs">{{ tag.name }}</el-tag>
            </template>
            <template v-else>无标签</template>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="detailTemplate.status === 'enabled' ? 'success' : 'info'" size="small">
              {{ detailTemplate.status === 'enabled' ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(detailTemplate.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="detailTemplate.content_type === 'image_text'" label="图片尺寸比例">
            {{ detailTemplate.image_size_ratio || '-' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="detailTemplate.content_type === 'image_text'" label="水印设置">
            {{ detailTemplate.add_watermark !== false ? '是' : '否' }}
          </el-descriptions-item>
          <el-descriptions-item label="提示词创意" :span="2">
            {{ detailTemplate.description || '无' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="detailTemplate.prompt_template" label="提示词指令" :span="2">
            <div class="prompt-template-box">{{ detailTemplate.prompt_template }}</div>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="getTemplateImageCount(detailTemplate) > 0" class="detail-image mt-md">
          <div class="detail-image-title">参考图片 ({{ getTemplateImageCount(detailTemplate) }})</div>
          <div class="detail-image-list">
            <el-image
              v-for="(imgUrl, index) in getTemplateImages(detailTemplate)"
              :key="index"
              :src="getFullImageUrl(imgUrl)"
              fit="contain"
              class="detail-full-image"
              :preview-src-list="getTemplateImages(detailTemplate).map(url => getFullImageUrl(url))"
              :initial-index="index"
            >
              <template #error>
                <div class="image-placeholder-large">
                  <el-icon :size="48" color="#909399"><Picture /></el-icon>
                  <span>图片加载失败</span>
                </div>
              </template>
            </el-image>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 批量迁移素材弹窗 -->
    <el-dialog v-model="showBatchMigrateDialog" :title="isSuperAdmin ? '批量迁移素材' : '批量迁移标签'" width="550px">
      <div class="batch-migrate-content">
        <p>已选择 <strong>{{ selectedIds.length }}</strong> 个素材</p>
        <el-form label-width="100px" class="mt-md">
          <!-- 超级管理员：选择目标管理员 -->
          <el-form-item v-if="isSuperAdmin" label="目标管理员" required>
            <el-select
              v-model="batchMigrateTargetAdminId"
              placeholder="请选择目标管理员"
              style="width: 100%;"
              @change="handleBatchMigrateAdminChange"
            >
              <el-option
                v-for="operator in operators"
                :key="operator.id"
                :label="operator.nickname || operator.userid"
                :value="operator.id"
              />
            </el-select>
          </el-form-item>
          <!-- 选择目标平台（超级管理员必选，创作管理员必选） -->
          <el-form-item label="目标平台" required>
            <el-select
              v-model="batchMigrateTargetPlatformId"
              placeholder="请选择目标平台"
              style="width: 100%;"
              @change="handleBatchMigratePlatformChange"
              :disabled="isSuperAdmin && !batchMigrateTargetAdminId"
            >
              <el-option
                v-for="platform in platformsForBatchMigrate"
                :key="platform.id"
                :label="platform.name"
                :value="platform.id"
              />
            </el-select>
          </el-form-item>
          <!-- 选择目标分类（必选） -->
          <el-form-item label="目标分类" required>
            <el-select
              v-model="batchMigrateTargetCategoryId"
              placeholder="请选择目标分类"
              style="width: 100%;"
              @change="handleBatchMigrateCategoryChange"
              :disabled="!batchMigrateTargetPlatformId"
            >
              <el-option
                v-for="category in categoriesForBatchMigrate"
                :key="category.id"
                :label="category.name"
                :value="category.id"
              />
            </el-select>
          </el-form-item>
          <!-- 选择目标标签（多选，必选） -->
          <el-form-item label="目标标签" required>
            <el-select
              v-model="batchMigrateTargetTagIds"
              multiple
              placeholder="请选择目标标签"
              style="width: 100%;"
              :disabled="!batchMigrateTargetCategoryId"
            >
              <el-option
                v-for="tag in tagsForBatchMigrate"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showBatchMigrateDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmBatchMigrate"
          :loading="saving"
          :disabled="selectedIds.length === 0 || !batchMigrateTargetPlatformId || !batchMigrateTargetCategoryId || batchMigrateTargetTagIds.length === 0"
        >
          确认迁移
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量复制素材弹窗 -->
    <el-dialog v-model="showBatchCopyDialog" :title="isSingleCopy ? '复制素材' : '批量复制素材'" width="550px">
      <div class="batch-copy-content">
        <p v-if="isSingleCopy">正在复制素材：<strong>{{ copyingTemplateForCopy }}</strong></p>
        <p v-else>已选择 <strong>{{ selectedIds.length }}</strong> 个素材，将复制为副本</p>
        <el-form label-width="100px" class="mt-md">
          <!-- 超级管理员：选择目标管理员 -->
          <el-form-item v-if="isSuperAdmin" label="目标管理员" required>
            <el-select
              v-model="batchCopyTargetAdminId"
              placeholder="请选择目标管理员"
              style="width: 100%;"
              @change="handleBatchCopyAdminChange"
            >
              <el-option
                v-for="operator in operators"
                :key="operator.id"
                :label="operator.nickname || operator.userid"
                :value="operator.id"
              />
            </el-select>
          </el-form-item>
          <!-- 选择目标平台（超级管理员必选，创作管理员必选） -->
          <el-form-item label="目标平台" required>
            <el-select
              v-model="batchCopyTargetPlatformId"
              placeholder="请选择目标平台"
              style="width: 100%;"
              @change="handleBatchCopyPlatformChange"
              :disabled="isSuperAdmin && !batchCopyTargetAdminId"
            >
              <el-option
                v-for="platform in platformsForBatchCopy"
                :key="platform.id"
                :label="platform.name"
                :value="platform.id"
              />
            </el-select>
          </el-form-item>
          <!-- 选择目标分类（必选） -->
          <el-form-item label="目标分类" required>
            <el-select
              v-model="batchCopyTargetCategoryId"
              placeholder="请选择目标分类"
              style="width: 100%;"
              @change="handleBatchCopyCategoryChange"
              :disabled="!batchCopyTargetPlatformId"
            >
              <el-option
                v-for="category in categoriesForBatchCopy"
                :key="category.id"
                :label="category.name"
                :value="category.id"
              />
            </el-select>
          </el-form-item>
          <!-- 选择目标标签（多选，必选） -->
          <el-form-item label="目标标签" required>
            <el-select
              v-model="batchCopyTargetTagIds"
              multiple
              placeholder="请选择目标标签"
              style="width: 100%;"
              :disabled="!batchCopyTargetCategoryId"
            >
              <el-option
                v-for="tag in tagsForBatchCopy"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <el-alert
          type="info"
          :closable="false"
          class="mt-md"
        >
          复制后的素材名称将自动添加 "- 副本" 后缀
        </el-alert>
      </div>
      <template #footer>
        <el-button @click="showBatchCopyDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmBatchCopy"
          :loading="saving"
          :disabled="selectedIds.length === 0 || !batchCopyTargetPlatformId || !batchCopyTargetCategoryId || batchCopyTargetTagIds.length === 0"
        >
          确认复制
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Delete, Loading, Folder, PriceTag, Tickets, Close, Document, Picture, View, Download } from '@element-plus/icons-vue'
import { apiClient, type Template, type User, type TemplateAttachment, type OperationLogCreateParams } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

// 操作日志模块常量
const MODULE_TEMPLATES = 'templates'

// 记录操作日志
async function logOperation(params: OperationLogCreateParams) {
  try {
    await apiClient.createOperationLog(params)
  } catch (e) {
    console.error('Failed to log operation:', e)
  }
}

const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.userRole === 'super_admin')
const currentUserId = computed(() => authStore.user?.id)

// 图片 URL 处理辅助函数
// API 基础 URL（不含 /api/v1 路径）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:8000'

function getFullImageUrl(url: string | undefined): string {
  if (!url) return '/images/placeholder-template-thumb.png'
  // 如果已经是完整 URL，直接返回
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('blob:')) {
    return url
  }
  // 相对路径通过后端服务访问（与素材库保持一致）
  return `${API_BASE_URL}${url}`
}

// 获取模板缩略图（优先使用附件）
function getTemplateThumbnail(template: Template): string {
  if (template.attachments && template.attachments.length > 0) {
    const attachment = template.attachments[0]
    const url = attachment.thumbnail_url || attachment.file_url
    return getFullImageUrl(url)
  }
  // 向后兼容：使用 style_reference
  return getFullImageUrl(template.style_reference)
}

// 获取模板图片数量
function getTemplateImageCount(template: Template): number {
  if (template.attachments) {
    return template.attachments.filter(a => a.file_type === 'image').length
  }
  return template.image_count || 0
}

// 获取模板的所有图片URL
function getTemplateImages(template: Template): string[] {
  if (template.attachments && template.attachments.length > 0) {
    return template.attachments
      .filter(a => a.file_type === 'image')
      .map(a => a.file_url)
  } else if (template.style_reference) {
    return [template.style_reference]
  }
  return []
}

const searchKeyword = ref('')
const searchStatus = ref('')
const searchContentType = ref('')
const selectedAdminId = ref<number | null>(null)
const treeSelectedAdminId = ref<number | null>(null) // 树节点选择的管理员（不影响下拉框）
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const viewMode = ref('card')
const loading = ref(false)
const saving = ref(false)

// 分类标签数据（按管理员分组）
const categoryTreeData = ref<{ adminId?: number; adminName?: string; platforms?: any[]; id?: number; name?: string; color?: string; template_count?: number; category_count?: number; categories?: any[] }[]>([])
const operators = ref<User[]>([])

// 当前选中
const selectedPlatformId = ref<number | null>(null)
const selectedCategoryId = ref<number | null>(null)
const selectedTagId = ref<number | null>(null)

// 构建平台/分类/标签节点
function buildPlatformNode(platform: any) {
  const platformNode: any = {
    key: `platform_${platform.id}`,
    id: platform.id,
    name: platform.name,
    color: platform.color,
    type: 'platform',
    isSystem: false,
    count: platform.template_count || 0,
    template_count: platform.template_count || 0,
    category_count: platform.category_count || 0,
    children: []
  }

  // 添加该平台下的分类
  if (platform.categories) {
    platform.categories.forEach((category: any) => {
      const categoryNode: any = {
        key: `category_${category.id}`,
        id: category.id,
        name: category.name,
        color: category.color,
        type: 'category',
        isSystem: false,
        count: category.template_count || 0,
        template_count: category.template_count || 0,
        tagCount: category.tags?.length ?? 0,
        platformId: platform.id,
        children: []
      }

      // 添加该分类下的标签
      if (category.tags) {
        category.tags.forEach((tag: any) => {
          categoryNode.children.push({
            key: `tag_${tag.id}`,
            id: tag.id,
            name: tag.name,
            color: tag.color,
            type: 'tag',
            isSystem: tag.is_system || false,
            count: tag.template_count || 0,
            categoryId: category.id,
            platformId: platform.id,
            children: []
          })
        })
      }

      platformNode.children.push(categoryNode)
    })
  }

  return platformNode
}

// 树形数据（构建含管理员分组）
const categoryTree = computed(() => {
  const nodes: any[] = [
    {
      key: 'all',
      name: '全部分类标签',
      type: 'all',
      isSystem: true,
      children: []
    }
  ]

  // 判断当前是否为分组模式：超级管理员且未通过下拉框选择管理员
  // 注意：树节点选择的 admin（treeSelectedAdminId）不影响树形显示
  const isGroupedMode = isSuperAdmin.value &&
                        selectedAdminId.value === null &&
                        categoryTreeData.value.length > 0 &&
                        categoryTreeData.value[0]?.adminId !== undefined

  if (isGroupedMode) {
    // 分组模式：显示按管理员分组的树
    categoryTreeData.value.forEach(adminTree => {
      if (adminTree.adminId && adminTree.platforms) {
        const adminNode = {
          key: `admin_${adminTree.adminId}`,
          id: adminTree.adminId,
          name: adminTree.adminName || '未知管理员',
          type: 'admin',
          isSystem: false,
          children: [] as any[]
        }

        adminTree.platforms.forEach((platform: any) => {
          adminNode.children.push(buildPlatformNode(platform))
        })

        nodes.push(adminNode)
      }
    })
  } else {
    // 普通模式：直接显示平台（无论是选中了管理员还是非超级管理员）
    categoryTreeData.value.forEach(platform => {
      if (platform.id && platform.name) {
        nodes.push(buildPlatformNode(platform))
      }
    })
  }

  return nodes
})

const categoryTreeProps = {
  children: 'children',
  label: 'name'
}

// 弹窗状态
const showPlatformDialog = ref(false)
const showCategoryDialog = ref(false)
const showTagDialog = ref(false)
const showDeleteDialog = ref(false)
const showCreateDialog = ref(false)
const showImagePreview = ref(false)
const showBatchMigrateDialog = ref(false)
const showBatchCopyDialog = ref(false)
const isSingleCopy = ref(false)  // 是否单个复制模式
const copyingTemplateForCopy = ref('')  // 单个复制时显示的模板名称
const templateEditMode = ref(false)
const isLoadingTemplateForm = ref(false)  // 防止 watch 在 handleEdit 加载数据时干扰
const editingTemplate = ref<Template | null>(null)
const previewTemplate = ref<Template | null>(null)
const detailTemplate = ref<Template | null>(null)
const showDetailDialog = ref(false)
const deletingItem = ref<{
  type: string;
  id: number;
  name: string;
  template_count?: number;
  tagCount?: number;
} | null>(null)
const selectedCategory = ref<{ id: number; name: string; platformId: number } | null>(null)

// 批量迁移相关
const batchMigrateTargetTagIds = ref<number[]>([])
const batchMigrateTargetAdminId = ref<number | null>(null)
const batchMigrateTargetPlatformId = ref<number | null>(null)
const batchMigrateTargetCategoryId = ref<number | null>(null)

// 批量复制相关
const batchCopyTargetTagIds = ref<number[]>([])
const batchCopyTargetAdminId = ref<number | null>(null)
const batchCopyTargetPlatformId = ref<number | null>(null)
const batchCopyTargetCategoryId = ref<number | null>(null)

// 表单
const platformForm = reactive({
  name: '',
  description: '',
  color: '#8B7CF6'
})

const categoryForm = reactive({
  name: '',
  description: '',
  color: '#67C23A'
})

const tagForm = reactive({
  name: '',
  description: '',
  color: '#909399'
})

const templateForm = reactive({
  name: '',
  description: '',
  contentType: 'text' as 'text' | 'image_text' | 'video_text',
  styleReference: '',
  promptTemplate: '',
  platformId: null as number | null,
  categoryId: null as number | null,
  tagIds: [] as number[],
  images: [] as { url: string; file?: File; uploading?: boolean; attachmentId?: number }[],
  // 图片尺寸比例：1:1(2048x2048), 4:3(2304x1728), 16:9(2560x1440), 3:4(1728x2304), 9:16(1440x2560)
  imageSizeRatio: '' as '' | '1:1' | '4:3' | '16:9' | '3:4' | '9:16',
  // 是否添加水印
  addWatermark: true,
  // ===== 爆款模板新增字段 =====
  viralType: '' as string,  // 支持 20 种爆款类型
  productName: '',  // 产品名称（必填）
  productSellingPoints: '',
  // "auto" 表示随机选择
  openingSeedId: 'auto' as number | string | null,
  emotionSeedId: 'auto' as number | string | null,
  endingSeedId: 'auto' as number | string | null
})

// 编辑时要删除的附件ID列表
const deleteAttachmentIds = ref<number[]>([])

// ===== 创意种子数据 =====
interface CreativeSeed {
  id: number
  name: string
  seed_type: string
  template: string
  description: string
  example_phrases?: string[]
}

const openingSeeds = ref<CreativeSeed[]>([])
const emotionSeeds = ref<CreativeSeed[]>([])
const endingSeeds = ref<CreativeSeed[]>([])

// ===== 爆款类型配置 =====
interface ViralTypeOption {
  value: string
  label: string
  description: string
  keywords?: string[]
}

const viralTypeOptions = ref<ViralTypeOption[]>([])

// 加载爆款类型配置
async function loadViralTypes() {
  try {
    const response = await apiClient.getViralTypes()
    viralTypeOptions.value = response || []
  } catch (e) {
    console.error('Failed to load viral types:', e)
    // 如果 API 调用失败，使用完整的 20 种默认选项
    viralTypeOptions.value = [
      { value: 'seeding', label: '种草安利型', description: '强调产品优点和使用体验，激发购买欲望', keywords: ['推荐', '安利', '必入', '真香'] },
      { value: 'review', label: '测评对比型', description: '多产品横向对比，提供选购建议', keywords: ['测评', '对比', '横评', '选哪个'] },
      { value: 'tutorial', label: '教程攻略型', description: '详细的使用教程和操作指南', keywords: ['教程', '攻略', '怎么用', '新手必看'] },
      { value: 'sharing', label: '好物分享型', description: '真实的使用感受分享，像朋友聊天', keywords: ['分享', '用后感', '真实体验'] },
      { value: 'pain_point', label: '痛点解决方案', description: '针对具体问题提供解决方案', keywords: ['痛点', '解决', '救星', '必备'] },
      { value: 'story', label: '故事叙述型', description: '通过故事串联产品使用场景', keywords: ['故事', '经历', '从前', '后来'] },
      { value: 'lifestyle', label: '生活场景型', description: '展示产品融入日常生活的方式', keywords: ['日常', '生活', '习惯', '每天用'] },
      { value: 'before_after', label: '前后对比型', description: '使用前后的效果对比展示', keywords: ['对比', '使用前', '使用后', '变化'] },
      { value: 'unboxing', label: '开箱体验型', description: '展示产品开箱和初次使用体验', keywords: ['开箱', '到了', '第一眼', '拆箱'] },
      { value: 'faq', label: '答疑解惑型', description: '解答用户常见疑问和顾虑', keywords: ['疑问', '解答', '常见问题', '一次说清'] },
      { value: 'daily', label: '日常记录型', description: '记录日常生活中的产品使用', keywords: ['日常', '记录', 'vlog', '日常碎片'] },
      { value: 'collection', label: '合集盘点型', description: '多款产品的合集推荐和盘点', keywords: ['合集', '盘点', '清单', '一次说全'] },
      { value: 'hidden_gem', label: '宝藏发现型', description: '分享被低估或小众的好物', keywords: ['宝藏', '小众', '意外发现', '冷门'] },
      { value: 'guide', label: '新手指南型', description: '面向新手的入门指南', keywords: ['新手', '入门', '指南', '必看'] },
      { value: 'transform', label: '改造焕新型', description: '展示改造前后的变化', keywords: ['改造', '焕新', '变身', '翻新'] },
      { value: 'hack', label: '小妙招型', description: '分享实用的使用技巧和妙招', keywords: ['妙招', '技巧', '小窍门', '隐藏功能'] },
      { value: 'wishlist', label: '许愿清单型', description: '分享想要购买的产品清单', keywords: ['许愿', '清单', '种草', '想要'] },
      { value: 'comparison', label: '横评选购型', description: '同类产品对比帮助用户选购', keywords: ['选购', '横评', '对比', '哪个好'] },
      { value: 'diary', label: '日记打卡型', description: '记录使用过程的打卡日记', keywords: ['日记', '打卡', '记录', '坚持'] },
      { value: 'trend', label: '热门趋势型', description: '分享当下热门流行产品', keywords: ['热门', '趋势', '流行', '当下最火'] },
    ]
  }
}

// 加载创意种子列表
async function loadCreativeSeeds() {
  try {
    const response = await apiClient.getCreativeSeeds()
    const seeds = response.items || []
    openingSeeds.value = seeds.filter((s: CreativeSeed) => s.seed_type === 'opening')
    emotionSeeds.value = seeds.filter((s: CreativeSeed) => s.seed_type === 'emotion')
    endingSeeds.value = seeds.filter((s: CreativeSeed) => s.seed_type === 'ending')
  } catch (e) {
    console.error('Failed to load creative seeds:', e)
  }
}

// 获取种子预览文本
function getSeedPreview(seedId: number | string | null, type: 'opening' | 'emotion' | 'ending'): string {
  // "auto" 或 null/undefined 表示随机选择，不显示预览
  if (!seedId || seedId === 'auto') return ''
  const seeds = type === 'opening' ? openingSeeds.value : type === 'emotion' ? emotionSeeds.value : endingSeeds.value
  // 统一转换为字符串比较（后端 seed_id 已改为字符串类型）
  const seed = seeds.find(s => String(s.id) === String(seedId))
  if (!seed) return ''
  return seed.template || seed.description || ''
}

// 获取爆款类型描述
function getViralTypeDescription(value: string): string {
  const vt = viralTypeOptions.value.find(v => v.value === value)
  return vt?.description || ''
}

// 获取爆款类型显示名称
function getViralTypeLabel(value: string | undefined): string {
  if (!value) return ''
  if (value === 'auto') return '随机选择'
  const vt = viralTypeOptions.value.find(v => v.value === value)
  return vt?.label || value
}

// 获取种子名称（用于模板卡片显示）
function getSeedName(seedId: number | string | null | undefined, type: 'opening' | 'emotion' | 'ending'): string {
  if (!seedId) return ''
  if (seedId === 'auto') return '随机选择'
  const seeds = type === 'opening' ? openingSeeds.value : type === 'emotion' ? emotionSeeds.value : endingSeeds.value
  const seed = seeds.find(s => String(s.id) === String(seedId))
  return seed?.name || ''
}

// 展开平台列表（处理分组结构）
function getFlatPlatforms() {
  if (categoryTreeData.value.length === 0) return []
  const firstItem = categoryTreeData.value[0]
  // 如果有 platforms 属性，说明是分组结构
  if (firstItem.platforms !== undefined) {
    const flat: any[] = []
    categoryTreeData.value.forEach(group => {
      if (group.platforms) {
        flat.push(...group.platforms)
      }
    })
    return flat
  }
  // 否则直接是平台列表
  return categoryTreeData.value
}

// 可用分类和标签
const availableCategories = computed(() => {
  const categories: { id: number; name: string; platformId: number }[] = []
  const flatPlatforms = getFlatPlatforms()
  
  flatPlatforms.forEach(platform => {
    // 如果选择了平台，只显示该平台的分类
    if (templateForm.platformId && platform.id !== templateForm.platformId) {
      return
    }
    if (platform.categories) {
      platform.categories.forEach((cat: any) => {
        categories.push({ id: cat.id, name: cat.name, platformId: platform.id })
      })
    }
  })
  return categories
})

const availableTags = computed(() => {
  const tags: { id: number; name: string; categoryId: number }[] = []
  const flatPlatforms = getFlatPlatforms()
  
  flatPlatforms.forEach(platform => {
    // 如果选择了平台，只显示该平台的标签（与 availableCategories 保持一致）
    if (templateForm.platformId && platform.id !== templateForm.platformId) {
      return
    }
    
    if (platform.categories) {
      platform.categories.forEach((cat: any) => {
        if (cat.tags) {
          cat.tags.forEach((tag: any) => {
            tags.push({ id: tag.id, name: tag.name, categoryId: cat.id })
          })
        }
      })
    }
  })
  
  // 根据表单中选择的分类来过滤标签
  return tags.filter(t => !templateForm.categoryId || t.categoryId === templateForm.categoryId)
})

// 素材创作列表
const templateList = ref<Template[]>([])

// 获取分类树数据
async function fetchCategoryTree() {
  try {
    // 超级管理员：优先使用树节点选择的管理员，否则使用下拉框选择的管理员
    const effectiveAdminId = treeSelectedAdminId.value !== null ? treeSelectedAdminId.value : selectedAdminId.value
    console.log('[fetchCategoryTree] effectiveAdminId:', effectiveAdminId, 'treeSelectedAdminId:', treeSelectedAdminId.value, 'selectedAdminId:', selectedAdminId.value)

    if (isSuperAdmin.value && effectiveAdminId !== null) {
      if (effectiveAdminId === 0) {
        // 超级管理员自己的素材
        console.log('[fetchCategoryTree] Admin 0 selected - clearing tree')
        categoryTreeData.value = []
        return
      } else {
        // 选中了特定管理员
        console.log('[fetchCategoryTree] Fetching platform tree for admin:', effectiveAdminId)
        const result = await apiClient.getTemplatePlatformTree({ owner_operator_id: effectiveAdminId })
        console.log('[fetchCategoryTree] API result:', result)
        categoryTreeData.value = result.platforms?.map((p: any) => ({ ...p })) || []
        console.log('[fetchCategoryTree] categoryTreeData set to:', categoryTreeData.value)
        return
      }
    }

    // 未选择管理员：获取所有管理员的平台树，按管理员分组
    if (isSuperAdmin.value && operators.value.length > 0) {
      const adminTrees: any[] = []

      for (const operator of operators.value) {
        try {
          const result = await apiClient.getTemplatePlatformTree({ owner_operator_id: operator.id })
          if (result.platforms && result.platforms.length > 0) {
            adminTrees.push({
              adminId: operator.id,
              adminName: operator.nickname || operator.userid,
              platforms: result.platforms
            })
          }
        } catch (e) {
          console.warn(`获取管理员 ${operator.nickname} 的平台树失败:`, e)
        }
      }

      categoryTreeData.value = adminTrees
    } else {
      // 非超级管理员：直接获取自己的平台树
      const result = await apiClient.getTemplatePlatformTree({})
      categoryTreeData.value = result.platforms?.map((p: any) => ({ ...p })) || []
    }
  } catch (error: any) {
    console.error('获取分类树失败:', error)
    ElMessage.error('获取分类树失败')
  }
}

// 获取创作管理员列表（超级管理员用）
async function fetchOperators() {
  if (!isSuperAdmin.value) return
  try {
    const result = await apiClient.getOperators({ limit: 100 })
    operators.value = result.items
  } catch (error: any) {
    console.error('获取创作管理员列表失败:', error)
  }
}

// 获取素材创作列表
async function fetchTemplates() {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      limit: pageSize.value
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (searchStatus.value) params.status = searchStatus.value
    if (searchContentType.value) params.content_type = searchContentType.value
    if (selectedPlatformId.value) {
      params.platform_id = selectedPlatformId.value
    }
    if (selectedCategoryId.value) {
      params.category_id = selectedCategoryId.value
    }
    if (selectedTagId.value) {
      params.tag_id = selectedTagId.value
    }
    if (isSuperAdmin.value) {
      // 优先使用树节点选择的管理员，否则使用下拉框选择的管理员
      const effectiveAdminId = treeSelectedAdminId.value !== null ? treeSelectedAdminId.value : selectedAdminId.value
      if (effectiveAdminId !== null) {
        params.owner_operator_id = effectiveAdminId
      }
    }

    console.log('[fetchTemplates] Request params:', params)
    const result = await apiClient.getTemplates(params)
    console.log('[fetchTemplates] Response:', { total: result.total, itemsCount: result.items?.length })
    // DEBUG: 检查第一个模板的种子ID字段
    if (result.items?.length > 0) {
      const first = result.items[0] as any
      console.log('[fetchTemplates] First template seed IDs:', {
        id: first.id,
        opening_seed_id: first.opening_seed_id,
        emotion_seed_id: first.emotion_seed_id,
        ending_seed_id: first.ending_seed_id
      })
    }
    templateList.value = result.items
    total.value = result.total
  } catch (error: any) {
    console.error('[fetchTemplates] Error:', error)
    ElMessage.error(error.message || '获取素材创作列表失败')
  } finally {
    loading.value = false
  }
}

// 初始化
onMounted(async () => {
  // 超级管理员需要先加载 operators 列表，再获取模板列表
  if (isSuperAdmin.value) {
    await fetchOperators()
  }
  fetchTemplates()
  fetchCategoryTree()
  loadCreativeSeeds()  // 加载创意种子列表
  loadViralTypes()     // 加载爆款类型配置
})

// 管理员筛选变更处理
function handleAdminChange() {
  console.log('[handleAdminChange] selectedAdminId changed to:', selectedAdminId.value, 'treeSelectedAdminId before:', treeSelectedAdminId.value)
  // 清空树选择的管理员ID，因为下拉框选择优先
  treeSelectedAdminId.value = null
  selectedPlatformId.value = null
  selectedCategoryId.value = null
  selectedTagId.value = null
  currentPage.value = 1
  console.log('[handleAdminChange] After reset - treeSelectedAdminId:', treeSelectedAdminId.value)
  fetchCategoryTree()
  fetchTemplates()
}

// 树节点点击
function handleNodeClick(data: any) {
  // 调试日志
  console.log('handleNodeClick called with:', { type: data.type, id: data.id, platformId: data.platformId, categoryId: data.categoryId })

  // 确保 id 是有效的数字
  const nodeId = typeof data.id === 'number' ? data.id : null
  console.log('nodeId:', nodeId)

  if (data.type === 'all') {
    // 重置所有筛选条件，包括树选择的管理员
    treeSelectedAdminId.value = null
    selectedPlatformId.value = null
    selectedCategoryId.value = null
    selectedTagId.value = null
    console.log('Type: all - cleared all selections, including treeSelectedAdminId')
  } else if (data.type === 'platform') {
    selectedPlatformId.value = nodeId
    selectedCategoryId.value = null
    selectedTagId.value = null
    console.log('Type: platform - set selectedPlatformId to', nodeId)
  } else if (data.type === 'category') {
    selectedPlatformId.value = data.platformId || null
    selectedCategoryId.value = nodeId
    selectedTagId.value = null
    console.log('Type: category - set platformId to', data.platformId, 'categoryId to', nodeId)
  } else if (data.type === 'tag' || data.type === 'no_tag') {
    selectedPlatformId.value = data.platformId || null
    selectedCategoryId.value = data.categoryId || null
    selectedTagId.value = nodeId
    console.log('Type: tag - set platformId to', data.platformId, 'categoryId to', data.categoryId, 'tagId to', nodeId)
  } else if (data.type === 'admin') {
    // 点击管理员节点：设置树选择的管理员用于筛选数据，但保持显示全部树形
    console.log('[handleNodeClick] admin node clicked, id:', nodeId)
    treeSelectedAdminId.value = nodeId
    // 不清空 selectedAdminId（下拉框保持不变）
    // 不调用 fetchCategoryTree()，保持树形列表不变
    selectedPlatformId.value = null
    selectedCategoryId.value = null
    selectedTagId.value = null
    console.log('[handleNodeClick] set treeSelectedAdminId to', nodeId, ', keep categoryTree unchanged')
    // 仅刷新模板列表（使用该管理员筛选）
    fetchTemplates()
    return
  } else {
    console.log('Unknown type:', data.type)
  }
  currentPage.value = 1
  fetchTemplates()
}

// 添加平台
function handleAddPlatform() {
  platformForm.name = ''
  platformForm.description = ''
  platformForm.color = '#2563EB'
  showPlatformDialog.value = true
}

async function handleSavePlatform() {
  if (!platformForm.name.trim()) {
    ElMessage.warning('请输入平台名称')
    return
  }
  saving.value = true
  try {
    await apiClient.createTemplatePlatform({
      name: platformForm.name,
      description: platformForm.description || undefined,
      color: platformForm.color
    })
    ElMessage.success('平台创建成功')
    showPlatformDialog.value = false
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '创建平台失败')
  } finally {
    saving.value = false
  }
}

// 添加分类
function handleAddCategory(data: any) {
  selectedPlatformId.value = data.id
  categoryForm.name = ''
  categoryForm.description = ''
  categoryForm.color = '#67C23A'
  showCategoryDialog.value = true
}

async function handleSaveCategory() {
  if (!categoryForm.name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  if (!selectedPlatformId.value) {
    ElMessage.warning('请选择所属平台')
    return
  }
  saving.value = true
  try {
    await apiClient.createTemplateCategory({
      name: categoryForm.name,
      platform_id: selectedPlatformId.value,
      description: categoryForm.description || undefined,
      color: categoryForm.color
    })
    ElMessage.success('分类创建成功')
    showCategoryDialog.value = false
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '创建分类失败')
  } finally {
    saving.value = false
  }
}

// 删除平台
async function handleDeletePlatform(data: any) {
  deletingItem.value = { type: 'platform', id: data.id, name: data.name }
  // 查询平台下的模板数量
  try {
    const stats = await apiClient.getTemplatePlatformStats(data.id)
    deletingItem.value = { type: 'platform', id: data.id, name: data.name, template_count: stats.template_count || 0 }
  } catch (error: any) {
    console.error('获取平台统计失败:', error)
    deletingItem.value = { type: 'platform', id: data.id, name: data.name, template_count: 0 }
  }
  showDeleteDialog.value = true
}

// 删除分类
async function handleRemoveCategory(data: any) {
  if (data.isSystem) {
    ElMessage.warning('系统默认分类不可删除')
    return
  }
  // 查询分类下的模板数量
  try {
    const stats = await apiClient.getTemplateCategoryStats(data.id)
    deletingItem.value = { type: 'category', id: data.id, name: data.name, template_count: stats.template_count || 0, tagCount: stats.tag_count || data.tagCount }
  } catch (error: any) {
    deletingItem.value = { type: 'category', id: data.id, name: data.name, template_count: 0, tagCount: data.tagCount }
  }
  showDeleteDialog.value = true
}

// 添加标签
function handleAddTag(data: any) {
  selectedCategory.value = { id: data.id, name: data.name, platformId: data.platformId }
  tagForm.name = ''
  tagForm.description = ''
  tagForm.color = '#909399'
  showTagDialog.value = true
}

async function handleSaveTag() {
  if (!tagForm.name.trim()) {
    ElMessage.warning('请输入标签名称')
    return
  }
  if (!selectedCategory.value?.id) {
    ElMessage.warning('请选择所属分类')
    return
  }
  saving.value = true
  try {
    const newTag = await apiClient.createTemplateTag({
      name: tagForm.name,
      category_id: selectedCategory.value.id,
      description: tagForm.description || undefined,
      color: tagForm.color
    })
    ElMessage.success('标签创建成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_TEMPLATES,
      action: 'create',
      description: `创建模板标签：${tagForm.name}`,
      table_name: 'template_tag',
      record_id: newTag?.id,
      new_value: {
        name: tagForm.name,
        category_id: selectedCategory.value.id,
        description: tagForm.description,
        color: tagForm.color
      }
    })
    showTagDialog.value = false
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '创建标签失败')
  } finally {
    saving.value = false
  }
}

// 删除标签
async function handleRemoveTag(data: any) {
  if (data.isSystem) {
    ElMessage.warning('系统默认标签不可删除')
    return
  }
  // 查询标签下的模板数量
  try {
    const stats = await apiClient.getTemplateTagStats(data.id)
    deletingItem.value = { type: 'tag', id: data.id, name: data.name, template_count: stats.template_count || 0 }
  } catch (error: any) {
    deletingItem.value = { type: 'tag', id: data.id, name: data.name, template_count: 0 }
  }
  showDeleteDialog.value = true
}

// 确认删除
async function handleConfirmDelete() {
  if (!deletingItem.value) return

  // 检查是否有模板关联
  if ((deletingItem.value.template_count || 0) > 0) {
    ElMessage.warning(`该${deletingItem.value.type === 'platform' ? '平台' : deletingItem.value.type === 'category' ? '分类' : '标签'}下有 ${deletingItem.value.template_count} 个素材，请先迁移或删除所有素材`)
    return
  }

  try {
    const itemType = deletingItem.value.type
    const itemId = deletingItem.value.id
    const itemName = deletingItem.value.name
    if (deletingItem.value.type === 'platform') {
      await apiClient.deleteTemplatePlatform(deletingItem.value.id)
      ElMessage.success('平台已删除')
    } else if (deletingItem.value.type === 'category') {
      await apiClient.deleteTemplateCategory(deletingItem.value.id)
      ElMessage.success('分类已删除')
    } else {
      await apiClient.deleteTemplateTag(deletingItem.value.id)
      ElMessage.success('标签已删除')
    }
    // 记录操作日志
    await logOperation({
      module: MODULE_TEMPLATES,
      action: 'delete',
      description: `删除模板${itemType === 'platform' ? '平台' : itemType === 'category' ? '分类' : '标签'}：${itemName}`,
      table_name: itemType === 'platform' ? 'template_platform' : itemType === 'category' ? 'template_category' : 'template_tag',
      record_id: itemId,
      old_value: { name: itemName }
    })
    showDeleteDialog.value = false
    deletingItem.value = null
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '删除失败')
  }
}

// 工具函数
function getContentTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    'text': '纯文本',
    'image_text': '图文',
    'video_text': '视频文案'
  }
  return labels[type] || type
}

// 获取模板的平台名称
function getTemplatePlatformName(template: Template): string {
  const t = template as any
  if (t.platform?.name) {
    return t.platform.name
  }
  if (t.platform_id) {
    return `平台 #${t.platform_id}`
  }
  return '-'
}

// 获取管理员名称（用于超级管理员视图显示）
function getAdminName(adminId: number): string {
  const admin = operators.value.find(op => op.id === adminId)
  if (admin) {
    return admin.nickname || admin.userid || '未知'
  }
  return '未知'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getTextSnippet(text?: string): string {
  if (!text) return ''
  return text.length > 50 ? text.substring(0, 50) + '...' : text
}

async function handleToggleStatus(template: Template) {
  try {
    const newStatus = template.status === 'enabled' ? 'disabled' : 'enabled'
    await apiClient.updateTemplate(template.id, { status: newStatus })
    ElMessage.success(newStatus === 'enabled' ? '已启用' : '已禁用')
    fetchTemplates()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

async function handleDelete(template: Template) {
  try {
    await ElMessageBox.confirm(
      `确定要删除素材创作「${template.name}」吗？此操作不可恢复！`,
      '确认删除',
      { type: 'warning' }
    )
    const oldValue = {
      name: template.name,
      content_type: template.content_type,
      description: template.description
    }
    await apiClient.deleteTemplate(template.id)
    ElMessage.success('素材创作删除成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_TEMPLATES,
      action: 'delete',
      description: `删除模板：${template.name}`,
      table_name: 'template',
      record_id: template.id,
      old_value: oldValue
    })
    fetchTemplates()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除素材创作失败')
    }
  }
}

// 列表视图批量操作
const selectAll = ref(false)
const selectedIds = ref<number[]>([])

const handleSelectionChange = (selection: Template[]) => {
  selectedIds.value = selection.map(item => item.id)
  selectAll.value = selection.length === templateList.value.length && templateList.value.length > 0
}

const handleSelectAll = (checked: boolean) => {
  selectAll.value = checked
  if (checked) {
    selectedIds.value = templateList.value.map(t => t.id)
  } else {
    selectedIds.value = []
  }
}

// 图片预览
function handlePreviewImage(template: Template) {
  previewTemplate.value = template
  showImagePreview.value = true
}

function downloadTemplateImage(imgUrl?: string) {
  if (!imgUrl && !previewTemplate.value?.style_reference) return
  const url = imgUrl || previewTemplate.value?.style_reference
  if (!url) return
  const link = document.createElement('a')
  link.href = getFullImageUrl(url)
  link.download = `${previewTemplate.value?.name || 'template'}.jpg`
  link.click()
}

// 批量操作相关

// ==================== 批量操作级联选择数据源 ====================

// 获取管理员的平台列表（超级管理员选择目标管理员后用）
function getAdminPlatforms(adminId: number | null) {
  if (!adminId) return []
  const adminTree = categoryTreeData.value.find(
    item => 'adminId' in item && item.adminId === adminId
  )
  if (adminTree && 'platforms' in adminTree && adminTree.platforms) {
    return adminTree.platforms
  }
  return []
}

// 批量复制用：可用平台列表（根据选择的管理员动态获取）
const platformsForBatchCopy = computed(() => {
  if (isSuperAdmin.value) {
    return getAdminPlatforms(batchCopyTargetAdminId.value)
  }
  // 创作管理员直接使用当前用户的平台
  return getFlatPlatforms()
})

// 批量迁移用：可用平台列表
const platformsForBatchMigrate = computed(() => {
  if (isSuperAdmin.value) {
    return getAdminPlatforms(batchMigrateTargetAdminId.value)
  }
  return getFlatPlatforms()
})

// 批量复制用：可用分类列表（根据选择的平台动态获取）
const categoriesForBatchCopy = computed(() => {
  if (!batchCopyTargetPlatformId.value) return []
  const platforms = platformsForBatchCopy.value
  const platform = platforms.find((p: any) => p.id === batchCopyTargetPlatformId.value)
  if (platform && platform.categories) {
    return platform.categories
  }
  return []
})

// 批量迁移用：可用分类列表
const categoriesForBatchMigrate = computed(() => {
  if (!batchMigrateTargetPlatformId.value) return []
  const platforms = platformsForBatchMigrate.value
  const platform = platforms.find((p: any) => p.id === batchMigrateTargetPlatformId.value)
  if (platform && platform.categories) {
    return platform.categories
  }
  return []
})

// 批量复制用：可用标签列表（根据选择的分类动态获取）
const tagsForBatchCopy = computed(() => {
  if (!batchCopyTargetCategoryId.value) return []
  const categories = categoriesForBatchCopy.value
  const category = categories.find((c: any) => c.id === batchCopyTargetCategoryId.value)
  if (category && category.tags) {
    return category.tags
  }
  return []
})

// 批量迁移用：可用标签列表
const tagsForBatchMigrate = computed(() => {
  if (!batchMigrateTargetCategoryId.value) return []
  const categories = categoriesForBatchMigrate.value
  const category = categories.find((c: any) => c.id === batchMigrateTargetCategoryId.value)
  if (category && category.tags) {
    return category.tags
  }
  return []
})

// 批量启用
async function handleBatchEnable() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要启用的素材')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要启用选中的 ${selectedIds.value.length} 个素材吗？`,
      '批量启用',
      { type: 'info' }
    )
    await apiClient.batchUpdateTemplateStatus(selectedIds.value, 'enabled')
    ElMessage.success(`已成功启用 ${selectedIds.value.length} 个素材`)
    selectedIds.value = []
    selectAll.value = false
    fetchTemplates()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '批量启用失败')
    }
  }
}

// 批量禁用
async function handleBatchDisable() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要禁用的素材')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要禁用选中的 ${selectedIds.value.length} 个素材吗？`,
      '批量禁用',
      { type: 'warning' }
    )
    await apiClient.batchUpdateTemplateStatus(selectedIds.value, 'disabled')
    ElMessage.success(`已成功禁用 ${selectedIds.value.length} 个素材`)
    selectedIds.value = []
    selectAll.value = false
    fetchTemplates()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '批量禁用失败')
    }
  }
}

// 批量复制
function handleBatchCopy() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要复制的素材')
    return
  }
  batchCopyTargetTagIds.value = []
  batchCopyTargetAdminId.value = null
  batchCopyTargetPlatformId.value = null
  batchCopyTargetCategoryId.value = null
  showBatchCopyDialog.value = true
}

async function confirmBatchCopy() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要复制的素材')
    return
  }
  if (batchCopyTargetTagIds.value.length === 0) {
    ElMessage.warning('请选择目标标签')
    return
  }

  saving.value = true
  try {
    if (isSingleCopy.value) {
      // 单个复制模式：调用单个复制API
      const templateId = selectedIds.value[0]
      const params: any = {}

      // 目标平台和分类（必选）
      params.target_platform_id = batchCopyTargetPlatformId.value
      params.target_category_id = batchCopyTargetCategoryId.value

      // 超级管理员：添加目标管理员参数
      if (isSuperAdmin.value && batchCopyTargetAdminId.value) {
        params.target_operator_id = batchCopyTargetAdminId.value
      }

      // 目标标签（必选）
      params.target_tag_ids = batchCopyTargetTagIds.value

      await apiClient.copyTemplate(templateId, params)
      ElMessage.success('素材创作复制成功')
    } else {
      // 批量复制模式：调用批量复制API
      const params: any = {
        template_ids: selectedIds.value
      }

      // 目标平台和分类（必选）
      params.target_platform_id = batchCopyTargetPlatformId.value
      params.target_category_id = batchCopyTargetCategoryId.value

      // 超级管理员：添加目标管理员参数
      if (isSuperAdmin.value && batchCopyTargetAdminId.value) {
        params.target_operator_id = batchCopyTargetAdminId.value
      }

      // 目标标签（必选）
      params.target_tag_ids = batchCopyTargetTagIds.value

      await apiClient.batchCopyTemplates(params)
      ElMessage.success(`已成功复制 ${selectedIds.value.length} 个素材`)
      selectAll.value = false
    }

    showBatchCopyDialog.value = false
    selectedIds.value = []
    isSingleCopy.value = false  // 重置为批量复制模式
    fetchTemplates()
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '复制失败')
  } finally {
    saving.value = false
  }
}

// 批量迁移
function handleBatchMigrate() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要迁移的素材')
    return
  }
  batchMigrateTargetTagIds.value = []
  batchMigrateTargetAdminId.value = null
  batchMigrateTargetPlatformId.value = null
  batchMigrateTargetCategoryId.value = null
  showBatchMigrateDialog.value = true
}

// 超级管理员切换目标管理员时：清空已选平台、分类、标签
function handleBatchMigrateAdminChange() {
  batchMigrateTargetPlatformId.value = null
  batchMigrateTargetCategoryId.value = null
  batchMigrateTargetTagIds.value = []
}

// 超级管理员切换目标管理员时：清空已选平台、分类、标签（批量复制用）
function handleBatchCopyAdminChange() {
  batchCopyTargetPlatformId.value = null
  batchCopyTargetCategoryId.value = null
  batchCopyTargetTagIds.value = []
}

// 切换平台时：清空已选分类、标签（批量迁移用）
function handleBatchMigratePlatformChange() {
  batchMigrateTargetCategoryId.value = null
  batchMigrateTargetTagIds.value = []
}

// 切换平台时：清空已选分类、标签（批量复制用）
function handleBatchCopyPlatformChange() {
  batchCopyTargetCategoryId.value = null
  batchCopyTargetTagIds.value = []
}

// 切换分类时：清空已选标签（批量迁移用）
function handleBatchMigrateCategoryChange() {
  batchMigrateTargetTagIds.value = []
}

// 切换分类时：清空已选标签（批量复制用）
function handleBatchCopyCategoryChange() {
  batchCopyTargetTagIds.value = []
}

async function confirmBatchMigrate() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要迁移的素材')
    return
  }
  if (batchMigrateTargetTagIds.value.length === 0) {
    ElMessage.warning('请选择目标标签')
    return
  }

  saving.value = true
  try {
    if (isSuperAdmin.value) {
      // 超级管理员：调用批量迁移API（素材所有权转移）
      await apiClient.batchTransferTemplates(
        selectedIds.value,
        batchMigrateTargetAdminId.value!,
        batchMigrateTargetPlatformId.value!,
        batchMigrateTargetCategoryId.value!,
        batchMigrateTargetTagIds.value
      )
      ElMessage.success(`已成功迁移 ${selectedIds.value.length} 个素材`)
    } else {
      // 创作管理员：调用批量更新标签API
      // 逐个更新素材标签
      for (const templateId of selectedIds.value) {
        await apiClient.updateTemplate(templateId, {
          platform_id: batchMigrateTargetPlatformId.value!,
          category_id: batchMigrateTargetCategoryId.value!,
          tag_ids: batchMigrateTargetTagIds.value
        })
      }
      ElMessage.success(`已成功更新 ${selectedIds.value.length} 个素材的标签`)
    }
    showBatchMigrateDialog.value = false
    selectedIds.value = []
    selectAll.value = false
    fetchTemplates()
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '批量迁移失败')
  } finally {
    saving.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTemplates()
}

const handleEdit = (template: Template) => {
  // DEBUG: 打印接收到的种子ID
  console.log('[handleEdit] Template received:', {
    id: template.id,
    opening_seed_id: (template as any).opening_seed_id,
    emotion_seed_id: (template as any).emotion_seed_id,
    ending_seed_id: (template as any).ending_seed_id
  })
  templateEditMode.value = true
  isLoadingTemplateForm.value = true
  editingTemplate.value = template

  // 重置要删除的附件列表
  deleteAttachmentIds.value = []

  // 加载已有图片（优先使用 attachments）
  const images: { url: string; file?: File; uploading?: boolean; attachmentId?: number }[] = []

  if (template.attachments && template.attachments.length > 0) {
    template.attachments
      .filter(a => a.file_type === 'image')
      .forEach(attachment => {
        images.push({
          url: getFullImageUrl(attachment.file_url),
          attachmentId: attachment.id
        })
      })
  } else if (template.style_reference) {
    // 向后兼容：使用 style_reference
    images.push({ url: getFullImageUrl(template.style_reference) })
  }

  // 获取平台ID和分类ID
  // 优先级：1. template.category  2. template.platform_id  3. 从标签的 category 获取
  let platformId: number | null = template.platform_id || null
  let categoryId: number | null = null

  // 优先从 template.category 获取
  if (template.category) {
    categoryId = template.category.id
    const categoryPlatformId = template.category.platform?.id || (template.category as any).template_platform_id
    if (categoryPlatformId) {
      platformId = categoryPlatformId
    }
  }
  // 兼容：从标签的 category 获取
  if (!platformId && template.tags?.length) {
    const firstTag = template.tags[0]
    if (firstTag.category) {
      const tagCategoryPlatformId = firstTag.category.platform?.id || (firstTag.category as any).template_platform_id
      if (tagCategoryPlatformId) {
        platformId = tagCategoryPlatformId
      }
      categoryId = firstTag.category.id
    }
  }

  Object.assign(templateForm, {
    name: template.name,
    styleReference: template.style_reference || '',
    promptTemplate: template.prompt_template || '',
    description: template.description || '',
    contentType: template.content_type,
    platformId: platformId,
    categoryId: categoryId,
    tagIds: template.tags?.map(t => t.id) || [],  // 直接设置标签（与 Material 保持一致）
    images: images,
    imageSizeRatio: template.image_size_ratio || '',
    addWatermark: template.add_watermark !== undefined ? template.add_watermark : true,
    // ===== 爆款模板字段 =====
    // 爆款类型：如果没有指定（null/undefined/空字符串），则默认为 'auto'（随机选择）
    viralType: (template as any).viral_type || 'auto',
    productName: (template as any).product_name || '',
    productSellingPoints: (template as any).product_selling_points || '',
    // 直接使用后端返回的值："auto" 或 seed ID（数字或字符串）
    openingSeedId: (template as any).opening_seed_id || 'auto',
    emotionSeedId: (template as any).emotion_seed_id || 'auto',
    endingSeedId: (template as any).ending_seed_id || 'auto'
  })

  // 数据加载完成后允许 watch 正常工作
  isLoadingTemplateForm.value = false
  showCreateDialog.value = true
}

const handleViewDetail = (template: Template) => {
  detailTemplate.value = template
  showDetailDialog.value = true
}

const handleCopy = async (template: Template) => {
  // 单个复制模式：复用批量复制对话框
  isSingleCopy.value = true
  copyingTemplateForCopy.value = template.name
  selectedIds.value = [template.id]

  // 重置批量复制目标选择状态
  batchCopyTargetTagIds.value = []
  batchCopyTargetAdminId.value = null
  batchCopyTargetPlatformId.value = null
  batchCopyTargetCategoryId.value = null

  showBatchCopyDialog.value = true

  // 记录操作日志
  await logOperation({
    module: MODULE_TEMPLATES,
    action: 'copy',
    description: `复制模板：${template.name}`,
    table_name: 'template',
    record_id: template.id,
    extra_data: { source_template_name: template.name }
  })
}

// 模板表单：平台变更时重置分类和标签
function handlePlatformChange() {
  templateForm.categoryId = null
  templateForm.tagIds = []
}

// 模板表单：分类变更时重置标签
function handleCategoryChange() {
  templateForm.tagIds = []
}

const handleSaveTemplate = async () => {
  if (!templateForm.name.trim()) {
    ElMessage.warning('请输入素材创作标题')
    return
  }
  if (!templateForm.description.trim()) {
    ElMessage.warning('请输入提示词创意')
    return
  }
  if (!templateForm.productName.trim()) {
    ElMessage.warning('请输入产品名称')
    return
  }
  if (!templateForm.platformId) {
    ElMessage.warning('请选择所属平台')
    return
  }
  if (templateForm.tagIds.length === 0) {
    ElMessage.warning('请选择所属标签')
    return
  }
  // 图文类型时，素材图片和图片尺寸比例都为必填
  if (templateForm.contentType === 'image_text') {
    if (templateForm.images.length === 0) {
      ElMessage.warning('请上传素材图片')
      return
    }
    if (!templateForm.imageSizeRatio) {
      ElMessage.warning('请选择图片尺寸比例')
      return
    }
  }
  saving.value = true
  try {
    // 提取文件对象
    const files = templateForm.images.map(img => img.file).filter(Boolean) as File[]

    if (templateEditMode.value && editingTemplate.value) {
      // 编辑模式：使用 updateTemplateWithAttachments，支持修改图片
      const oldValue = {
        name: editingTemplate.value.name,
        content_type: editingTemplate.value.content_type,
        description: editingTemplate.value.description
      }
      const newValue = {
        name: templateForm.name,
        content_type: templateForm.contentType || 'text',
        description: templateForm.description,
        platform_id: templateForm.platformId,
        tag_ids: templateForm.tagIds,
        image_size_ratio: templateForm.imageSizeRatio,
        add_watermark: templateForm.addWatermark
      }
      await apiClient.updateTemplateWithAttachments({
        id: editingTemplate.value.id,
        name: templateForm.name,
        product_name: templateForm.productName || '',
        content_type: templateForm.contentType || 'text',
        prompt_template: templateForm.promptTemplate || undefined,
        description: templateForm.description || undefined,
        platform_id: templateForm.platformId,
        tag_ids: templateForm.tagIds,
        delete_attachment_ids: deleteAttachmentIds.value.length > 0 ? deleteAttachmentIds.value : undefined,
        files: files.length > 0 ? files : undefined,
        image_size_ratio: templateForm.imageSizeRatio || undefined,
        add_watermark: templateForm.addWatermark,
        // ===== 爆款模板字段 =====
        // 爆款类型：空字符串转为 "auto" 表示随机选择
        viral_type: templateForm.viralType || 'auto',
        product_selling_points: templateForm.productSellingPoints ?? '',
        // "auto"表示随机选择，空字符串或null也转为"auto"
        opening_seed_id: templateForm.openingSeedId || 'auto',
        emotion_seed_id: templateForm.emotionSeedId || 'auto',
        ending_seed_id: templateForm.endingSeedId || 'auto'
      })
      ElMessage.success('素材创作已保存')
      // 记录操作日志
      await logOperation({
        module: MODULE_TEMPLATES,
        action: 'update',
        description: `更新模板：${templateForm.name}`,
        table_name: 'template',
        record_id: editingTemplate.value.id,
        old_value: oldValue,
        new_value: newValue
      })
    } else {
      // 创建模式：使用 uploadTemplate，支持文件上传（参考素材库实现）
      const newTemplate = await apiClient.uploadTemplate({
        name: templateForm.name,
        description: templateForm.description || '',
        content_type: templateForm.contentType || 'text',
        prompt_template: templateForm.promptTemplate || undefined,
        platform_id: templateForm.platformId,
        tag_ids: templateForm.tagIds,
        files: files.length > 0 ? files : undefined,
        image_size_ratio: templateForm.imageSizeRatio || undefined,
        add_watermark: templateForm.addWatermark,
        // ===== 爆款模板字段 =====
        // 爆款类型：空字符串转为 "auto" 表示随机选择
        viral_type: templateForm.viralType || 'auto',
        product_name: templateForm.productName || '产品',
        product_selling_points: templateForm.productSellingPoints ?? '',
        // "auto"表示随机选择，空字符串或null也转为"auto"
        opening_seed_id: templateForm.openingSeedId || 'auto',
        emotion_seed_id: templateForm.emotionSeedId || 'auto',
        ending_seed_id: templateForm.endingSeedId || 'auto'
      })
      ElMessage.success('素材创作已创建')
      // 记录操作日志
      await logOperation({
        module: MODULE_TEMPLATES,
        action: 'create',
        description: `创建模板：${templateForm.name}`,
        table_name: 'template',
        record_id: newTemplate?.id,
        new_value: {
          name: templateForm.name,
          content_type: templateForm.contentType || 'text',
          description: templateForm.description,
          platform_id: templateForm.platformId,
          tag_ids: templateForm.tagIds
        }
      })
    }
    showCreateDialog.value = false
    templateEditMode.value = false
    editingTemplate.value = null
    deleteAttachmentIds.value = []
    fetchTemplates()
  } catch (error: any) {
    ElMessage.error(error.message || '保存素材创作失败')
  } finally {
    saving.value = false
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 个素材创作吗？此操作不可恢复！`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )
    // 记录删除前的模板信息
    const deletedTemplates = templateList.value
      .filter(t => selectedIds.value.includes(t.id))
      .map(t => ({ id: t.id, name: t.name, content_type: t.content_type }))
    for (const id of selectedIds.value) {
      await apiClient.deleteTemplate(id)
    }
    ElMessage.success('批量删除成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_TEMPLATES,
      action: 'delete',
      description: `批量删除模板：${deletedTemplates.length}个模板`,
      table_name: 'template',
      extra_data: { deleted_templates: deletedTemplates }
    })
    selectedIds.value = []
    selectAll.value = false
    fetchTemplates()
  } catch {
  }
}

// 监听分类选择变化，切换分类时清空已选标签（仅在非编辑模式或手动切换时）
// 注意：不再使用 watch 监听 categoryId 变化来清空标签
// 改用 @change 事件（handleCategoryChange）处理，与 Material 保持一致

// 图片上传相关
const handleTemplateImageChange = (file: any) => {
  const rawFile = file.raw
  const isImage = rawFile.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return
  }

  // 检查文件大小 (20MB)
  const maxSize = 20 * 1024 * 1024
  if (rawFile.size > maxSize) {
    ElMessage.error(`图片文件大小不能超过 20MB，当前文件大小：${(rawFile.size / 1024 / 1024).toFixed(2)}MB`)
    return
  }

  // 只显示本地预览，不立即上传到服务器（参考素材库实现）
  const localUrl = URL.createObjectURL(rawFile)
  templateForm.images.push({ url: localUrl, file: rawFile })

  return false // 阻止自动上传
}

const removeTemplateImage = (index: number) => {
  const img = templateForm.images[index]
  // 如果是现有附件，记录要删除的ID
  if (img.attachmentId) {
    deleteAttachmentIds.value.push(img.attachmentId)
  }
  if (img.url.startsWith('blob:')) {
    URL.revokeObjectURL(img.url)
  }
  templateForm.images.splice(index, 1)
}

// 重置表单时清空图片和编辑状态
watch(showCreateDialog, (val) => {
  if (!val) {
    templateForm.images.forEach(img => {
      if (img.url.startsWith('blob:')) {
        URL.revokeObjectURL(img.url)
      }
    })
    templateForm.images = []
    deleteAttachmentIds.value = []
    // 关闭对话框时重置编辑状态
    templateEditMode.value = false
    editingTemplate.value = null
    // 重置爆款模板字段
    templateForm.viralType = ''
    templateForm.productSellingPoints = ''
    templateForm.openingSeedId = null
    templateForm.emotionSeedId = null
    templateForm.endingSeedId = null
  }
})

// 监听内容类型变化，当变为图文类型时自动设置图片尺寸比例为 1:1
// 注意：仅在创建新模板时自动设置，编辑时由 handleEdit 加载已有值
watch(() => templateForm.contentType, (newVal) => {
  // 加载数据期间不触发自动设置，由 handleEdit 确保正确的 imageSizeRatio
  if (isLoadingTemplateForm.value) return

  // 只有在创建模式且 imageSizeRatio 为空时自动设置默认值
  if (newVal === 'image_text' && !templateForm.imageSizeRatio && !templateEditMode.value) {
    templateForm.imageSizeRatio = '1:1'
  } else if (newVal !== 'image_text') {
    templateForm.imageSizeRatio = ''
  }
})
</script>

<style lang="scss" scoped>
// 导入高级设计规范样式
@import './templates.scss';

.template-list-view {
  padding: 0;
}

.category-panel {
  height: calc(100vh - 140px);
  overflow-y: auto;
}

.admin-filter {
  margin-bottom: 12px;
}

.panel-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.panel-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.custom-tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 8px;
}

.node-label {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;

  .label-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .system-badge {
    font-size: 10px;
    padding: 0 4px;
    background: #e6a23c;
    color: white;
    border-radius: 2px;
    line-height: 14px;
  }

  .count-badge {
    margin-left: auto;
    height: 18px;
    padding: 0 6px;
    font-size: 11px;
    line-height: 16px;
  }
}

.node-actions {
  display: none;
  gap: 8px;
}

.custom-tree-node:hover .node-actions {
  display: flex;
}

.action-icon {
  cursor: pointer;
  transition: color 0.2s;

  &.add {
    color: var(--color-primary);
    &:hover {
      color: #66b1ff;
    }
  }

  &.delete {
    color: #F56C6C;
    &:hover {
      color: #f89898;
    }
  }
}

.toolbar {
  margin-bottom: 16px;
}

.gap-md {
  gap: 12px;
}

.flex {
  display: flex;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mb-md {
  margin-bottom: 16px;
}

.mr-xs {
  margin-right: 4px;
}

.mt-lg {
  margin-top: 24px;
}

.image-count-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.view-tabs {
  margin-bottom: 16px;
}

.loading-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--text-placeholder);
}

.list-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 4px;
}

.selected-count {
  color: var(--color-primary);
  font-size: 14px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.template-card {
  :deep(.el-card__header) {
    padding: 8px 10px;
  }

  :deep(.el-card__body) {
    padding: 8px 10px;
  }

  .card-header {
    .template-name {
      font-weight: 500;
      color: var(--text-primary);
      font-size: 14px;
    }

    .header-tags {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }

  .template-preview {
    position: relative;
    height: 100px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 8px;

    .text-preview {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      padding: 12px;

      .text-snippet {
        margin-top: 8px;
        font-size: 12px;
        color: var(--text-secondary);
        text-align: center;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
    }

    .preview-image {
      width: 100%;
      height: 100%;
    }
  }
}

.template-info {
  .info-row {
    display: flex;
    align-items: center;
    margin-bottom: 4px;
    font-size: 12px;

    .label {
      color: var(--color-text-secondary);
      font-weight: 500;
      width: 60px;
      flex-shrink: 0;
    }

    .value {
      color: var(--color-text-primary);
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.template-actions {
  display: flex;
  justify-content: flex-end;
  flex-wrap: nowrap;
  gap: 0;
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--border-color);

  .el-button--small.is-link {
    padding: 1px 3px;
    font-size: 12px;
  }
}

.pagination {
  padding: $spacing-sm 0;
  margin-top: $spacing-md;
  white-space: nowrap;
  display: flex;
  align-items: center;
}

.total-text {
  color: var(--color-text-secondary);
  font-size: $font-size-sm;
  white-space: nowrap;
  font-size: 14px;
  white-space: nowrap;
}

// 图片上传区域样式
.image-upload-area {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.image-preview-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border-color);

  .preview-img {
    width: 100%;
    height: 100%;
  }

  .remove-icon {
    position: absolute;
    top: 4px;
    right: 4px;
    width: 20px;
    height: 20px;
    background: rgba(0, 0, 0, 0.5);
    color: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 12px;

    &:hover {
      background: rgba(0, 0, 0, 0.7);
    }
  }
}

.image-uploader {
  width: 100px;
  height: 100px;
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  cursor: pointer;

  :deep(.upload-placeholder) {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100px;
    height: 100px;
    color: var(--text-placeholder);

    .el-icon {
      font-size: 24px;
      margin-bottom: 4px;
    }

    span {
      font-size: 12px;
    }
  }

  &:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
  }
}

.upload-tip {
  margin-top: 8px;
  color: var(--text-placeholder);
  font-size: 12px;
}

// 图片预览相关样式（对标素材对标库）
.image-preview-wrapper {
  position: relative;
  height: 100%;
  cursor: pointer;
  overflow: hidden;

  &:hover {
    .image-hover-overlay {
      opacity: 1;
    }
  }
}

.image-hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
  font-size: 12px;
  gap: 4px;
}

.image-placeholder,
.image-placeholder-small {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
}

.image-placeholder {
  height: 100px;
}

.image-placeholder-small {
  width: 60px;
  height: 60px;
}

// 列表视图图片包装器
.list-image-wrapper {
  cursor: pointer;
  transition: transform 0.2s;

  &:hover {
    transform: scale(1.05);
  }
}

.list-image-count {
  position: absolute;
  bottom: 2px;
  right: 2px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 11px;
}

// 图片预览对话框样式（对标素材对标库样式，适配主题）
.image-preview-dialog {
  .preview-template-title {
    font-size: 16px;
    font-weight: 500;
    color: var(--text-primary);
    text-align: center;
  }

  .preview-image-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
    max-height: 600px;
    overflow-y: auto;
  }

  .preview-image-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    background: var(--bg-tertiary);
    border-radius: 8px;
  }

  .preview-full-image {
    width: 100%;
    height: 300px;
    background: var(--bg-secondary);
    border-radius: 4px;
  }

  .preview-image-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .image-index {
    color: var(--text-secondary);
    font-size: 13px;
  }

  .image-placeholder-large {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 300px;
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    gap: 8px;
  }
}

.template-detail {
  .prompt-template-box {
    max-height: 150px;
    overflow-y: auto;
    padding: 8px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    white-space: pre-wrap;
    font-size: 13px;
  }

  .detail-image {
    .detail-image-title {
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 8px;
      color: #303133;
    }

    .detail-image-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .detail-full-image {
      width: 100%;
      max-height: 300px;
      border-radius: 4px;
      background: #f5f7fa;
    }
  }
}

// 批量操作对话框样式
.batch-migrate-content,
.batch-copy-content {
  p {
    font-size: 14px;
    color: #606266;
    margin-bottom: 12px;
  }
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

// 创意种子预览样式 - 适配双主题
.seed-preview {
  margin-top: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  font-size: 12px;
  font-weight: normal;
  color: var(--text-secondary);
  border-left: 3px solid var(--primary-color);
}

// 爆款类型下拉选项样式 - 适配双主题
.viral-type-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 0;

  .viral-type-label {
    font-size: 14px;
    color: var(--text-secondary);
  }

  .viral-type-desc {
    font-size: 12px;
    color: var(--text-secondary);
    line-height: 1.0;
  }
}

// 爆款类型预览样式 - 与 seed-preview 保持一致
.viral-type-preview {
  margin-top: 8px;
  padding: 4px 4px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  font-size: 12px;
  font-weight: normal;
  color: var(--text-secondary);
  border-left: 3px solid var(--primary-color);
}
</style>
