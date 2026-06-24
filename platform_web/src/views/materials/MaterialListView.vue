<template>
  <div class="material-list-view">
    <h2 class="page-title">素材对标库</h2>

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
                  <el-icon v-if="data.type === 'admin'" :style="{ color: '#8B7CF6' }">
                    <Folder />
                  </el-icon>
                  <el-icon v-else-if="data.type === 'platform'" :style="{ color: data.color || '#8B7CF6' }">
                    <Folder />
                  </el-icon>
                  <el-icon v-else-if="data.type === 'category'" :style="{ color: data.color || '#67C23A' }">
                    <Tickets />
                  </el-icon>
                  <el-icon v-else-if="data.type === 'tag'" :style="{ color: data.color || '#909399' }">
                    <PriceTag />
                  </el-icon>
                  <span class="label-text">{{ node.label }}</span>
                  <span v-if="data.isSystem" class="system-badge">系统</span>
                  <span v-if="data.count !== undefined" class="count-badge">{{ data.count }}</span>
                </span>
                <span v-if="data.type === 'admin'" class="node-actions">
                  <!-- 管理员节点：无操作按钮 -->
                </span>
                <span v-else-if="data.type === 'platform'" class="node-actions">
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
                placeholder="搜索素材标题"
                :prefix-icon="Search"
                clearable
                style="width: 240px;"
                @keyup.enter="handleSearch"
              />
              <el-select v-model="searchType" placeholder="内容类型" clearable style="width: 120px;">
                <el-option label="全部" value="" />
                <el-option label="纯文本" value="text" />
                <el-option label="图文" value="image_text" />
              </el-select>
              <el-select v-model="searchStatus" placeholder="状态筛选" clearable style="width: 120px;">
                <el-option label="全部" value="" />
                <el-option label="可用" value="available" />
                <el-option label="已禁用" value="disabled" />
              </el-select>
              <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
            </div>
            <div class="toolbar-right flex gap-md">
              <el-button v-if="!isSuperAdmin" type="primary" :icon="Plus" @click="showUploadDialog = true">上传对标</el-button>
            </div>
          </div>

          <el-tabs v-model="viewMode" class="view-tabs">
            <el-tab-pane label="卡片视图" name="card">
              <div v-if="loading" class="loading-container">
                <el-icon class="is-loading" :size="32"><Loading /></el-icon>
                <span>加载中...</span>
              </div>
              <div v-else-if="materialList.length === 0" class="empty-container">
                <el-empty description="暂无素材数据" />
              </div>
              <div v-else class="material-grid">
                <el-card
                  v-for="material in materialList"
                  :key="material.id"
                  class="material-card"
                  shadow="hover"
                >
                  <template #header>
                    <div class="card-header flex-between">
                      <span class="material-title">{{ material.title }}</span>
                      <div class="header-tags">
                        <el-tag :type="material.status === 'available' ? 'success' : 'info'" size="small">
                          {{ material.status === 'available' ? '可用' : '已禁用' }}
                        </el-tag>
                      </div>
                    </div>
                  </template>
                  <div class="material-preview">
                    <div v-if="material.content_type === 'text'" class="text-preview">
                      <el-icon :size="48" color="#909399"><Document /></el-icon>
                      <div class="text-snippet">{{ getTextSnippet(material.text_content) }}</div>
                    </div>
                    <div v-else class="image-preview-wrapper" @click="handlePreviewImages(material)">
                      <el-image
                        :src="getThumbnail(material)"
                        fit="cover"
                        class="preview-image"
                      >
                        <template #error>
                          <div class="image-placeholder">
                            <el-icon :size="32" color="#909399"><Picture /></el-icon>
                          </div>
                        </template>
                      </el-image>
                      <div v-if="getImageCount(material) > 1" class="image-count-badge">
                        <el-icon><Picture /></el-icon>
                        <span>{{ getImageCount(material) }}</span>
                      </div>
                      <div class="image-hover-overlay">
                        <el-icon :size="24"><View /></el-icon>
                        <span>点击查看</span>
                      </div>
                    </div>
                  </div>
                  <div class="material-info">
                    <div class="info-row">
                      <span class="label">类型:</span>
                      <el-tag size="small" type="info">{{ getContentTypeLabel(material.content_type) }}</el-tag>
                    </div>
                    <div class="info-row">
                      <span class="label">标签:</span>
                      <span class="value">
                        <template v-if="material.tags && material.tags.length > 0">
                          <el-tag v-for="tag in material.tags" :key="tag.id" size="small" type="info" class="mr-xs">{{ tag.name }}</el-tag>
                        </template>
                        <template v-else>无标签</template>
                      </span>
                    </div>
                    <div class="info-row">
                      <span class="label">创建时间:</span>
                      <span class="value">{{ formatDate(material.created_at) }}</span>
                    </div>
                    <div v-if="isSuperAdmin" class="info-row">
                      <span class="label">所属管理:</span>
                      <span class="value">
                        <span v-if="material.owner_admin_id">{{ getOperatorName(material.owner_admin_id) }}</span>
                        <span v-else>无</span>
                      </span>
                    </div>
                  </div>
                  <div class="material-actions">
                    <el-button type="primary" link size="small" @click="handleEdit(material)">编辑</el-button>
                    <el-button type="info" link size="small" @click="handleViewDetail(material)">详情</el-button>
                    <el-button type="success" link size="small" @click="handleCopy(material)">复制</el-button>
                    <el-button
                      :type="material.status === 'available' ? 'warning' : 'success'"
                      link
                      size="small"
                      @click="handleToggleStatus(material)"
                    >
                      {{ material.status === 'available' ? '禁用' : '启用' }}
                    </el-button>
                    <el-button type="danger" link size="small" @click="handleDelete(material)">删除</el-button>
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
                <el-table :data="materialList" style="width: 100%" @selection-change="handleSelectionChange">
                  <el-table-column type="selection" width="55" />
                  <el-table-column label="预览" width="100">
                    <template #default="{ row }">
                      <el-icon v-if="row.content_type === 'text'" :size="32" color="#909399"><Document /></el-icon>
                      <div
                        v-else
                        class="list-image-wrapper"
                        @click="handlePreviewImages(row)"
                      >
                        <el-image
                          :src="getThumbnail(row)"
                          fit="cover"
                          style="width: 60px; height: 60px; border-radius: 4px; cursor: pointer;"
                        >
                          <template #error>
                            <div class="image-placeholder-small">
                              <el-icon :size="24" color="#909399"><Picture /></el-icon>
                            </div>
                          </template>
                        </el-image>
                        <div v-if="getImageCount(row) > 1" class="list-image-count">
                          {{ getImageCount(row) }}
                        </div>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column prop="title" label="素材标题" min-width="180" />
                  <el-table-column prop="content_type" label="类型" width="100">
                    <template #default="{ row }">
                      <el-tag size="small">{{ getContentTypeLabel(row.content_type) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column v-if="isSuperAdmin" label="所属管理员" width="120">
                    <template #default="{ row }">
                      <span v-if="row.owner_admin_id">{{ getOperatorName(row.owner_admin_id) }}</span>
                      <span v-else>无</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="标签" width="150">
                    <template #default="{ row }">
                      <template v-if="row.tags && row.tags.length > 0">
                        <el-tag v-for="tag in row.tags.slice(0, 2)" :key="tag.id" size="small" type="info" class="mr-xs">{{ tag.name }}</el-tag>
                        <span v-if="row.tags.length > 2" style="color: #909399; font-size: 12px;">+{{ row.tags.length - 2 }}</span>
                      </template>
                      <template v-else>无标签</template>
                    </template>
                  </el-table-column>
                  <el-table-column prop="status" label="状态" width="90">
                    <template #default="{ row }">
                      <el-tag :type="row.status === 'available' ? 'success' : 'info'" size="small">
                        {{ row.status === 'available' ? '可用' : '已禁用' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="created_at" label="创建时间" width="170">
                    <template #default="{ row }">
                      {{ formatDate(row.created_at) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" min-width="220" fixed="right">
                    <template #default="{ row }">
                      <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
                      <el-button type="info" link size="small" @click="handleViewDetail(row)">详情</el-button>
                      <el-button type="success" link size="small" @click="handleCopy(row)">复制</el-button>
                      <el-button
                        :type="row.status === 'available' ? 'warning' : 'success'"
                        link
                        size="small"
                        @click="handleToggleStatus(row)"
                      >
                        {{ row.status === 'available' ? '禁用' : '启用' }}
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
              @current-change="fetchMaterials"
              @size-change="fetchMaterials"
            />
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 添加平台弹窗 -->
    <el-dialog v-model="showPlatformDialog" title="添加平台" width="450px">
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

    <!-- 删除平台确认弹窗 -->
    <el-dialog v-model="showDeletePlatformDialog" title="确认删除平台" width="450px">
      <el-alert
        :title="`确定要删除平台「${deletingPlatform?.name}」吗？`"
        type="warning"
        :closable="false"
        show-icon
        class="mb-md"
      />
      <div v-if="deletingPlatform" class="delete-platform-info">
        <p>该平台包含：</p>
        <ul>
          <li>{{ deletingPlatform.category_count || 0 }} 个分类</li>
          <li>关联素材数：<strong>{{ deletingPlatform.material_count || 0 }}</strong></li>
        </ul>
        <p v-if="(deletingPlatform.material_count || 0) > 0" class="error-text">
          请先删除或迁移所有素材后再删除平台
        </p>
        <p v-else class="success-text">
          该平台下无素材，可以安全删除
        </p>
      </div>
      <template #footer>
        <el-button @click="showDeletePlatformDialog = false">取消</el-button>
        <el-button
          type="danger"
          @click="confirmDeletePlatform"
          :disabled="(deletingPlatform?.material_count || 0) > 0"
          :loading="deletingPlatformLoading"
        >
          确认删除
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加分类弹窗 -->
    <el-dialog v-model="showCategoryDialog" title="添加分类" width="450px">
      <el-form :model="categoryForm" label-width="100px">
        <el-form-item label="所属平台">
          <el-input :model-value="categoryForm.platformName" disabled />
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
    <el-dialog v-model="showTagDialog" title="添加素材标签" width="450px">
      <el-form :model="tagForm" label-width="100px">
        <el-form-item label="所属分类">
          <el-input :model-value="tagForm.categoryName" disabled />
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

    <!-- 上传素材对标弹窗 -->
    <el-dialog v-model="showUploadDialog" title="上传素材对标" width="650px">
      <el-form :model="uploadForm" label-width="100px" :rules="uploadFormRules" ref="uploadFormRef">
        <el-form-item label="素材标题" prop="title">
          <el-input v-model="uploadForm.title" placeholder="请输入素材标题" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="素材内容" prop="content">
          <el-input v-model="uploadForm.content" type="textarea" :rows="4" placeholder="请输入素材内容（必填）" />
        </el-form-item>
        <el-form-item label="内容类型" prop="content_type">
          <el-radio-group v-model="uploadForm.content_type">
            <el-radio value="text">纯文本</el-radio>
            <el-radio value="image_text">图文</el-radio>
          </el-radio-group>
        </el-form-item>
        <!-- 图文类型时显示图片上传 -->
        <el-form-item v-if="uploadForm.content_type === 'image_text'" label="素材图片" prop>
          <div class="image-upload-area">
            <div v-for="(img, index) in uploadForm.images" :key="index" class="image-preview-item">
              <el-image :src="img.url" fit="cover" class="preview-img" />
              <el-icon class="remove-icon" @click="removeUploadImage(index)"><Close /></el-icon>
            </div>
            <el-upload
              :show-file-list="false"
              :before-upload="beforeImageUpload"
              accept="image/*"
              class="image-uploader"
            >
              <div class="upload-placeholder">
                <el-icon><Plus /></el-icon>
                <span>添加图片</span>
              </div>
            </el-upload>
          </div>
          <div class="upload-tip">支持添加多张图片</div>
        </el-form-item>
        <el-form-item label="素材话题" prop="topic">
          <el-input v-model="uploadForm.topic" placeholder="请输入素材话题（必填）" maxlength="255" />
        </el-form-item>
        <el-form-item label="所属平台" prop="platform_id">
          <el-select v-model="uploadForm.platform_id" placeholder="请选择平台" clearable style="width: 100%;" @change="handleUploadPlatformChange">
            <el-option
              v-for="platform in getAllPlatforms()"
              :key="platform.id"
              :label="platform.name"
              :value="platform.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属分类" prop="category_id">
          <el-select v-model="uploadForm.category_id" placeholder="请先选择平台" clearable style="width: 100%;" @change="uploadForm.tag_ids = []" :disabled="!uploadForm.platform_id">
            <el-option
              v-for="category in uploadFormCategories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属标签" prop="tag_ids">
          <el-select v-model="uploadForm.tag_ids" multiple placeholder="请先选择分类" style="width: 100%;" clearable :disabled="!uploadForm.category_id">
            <el-option
              v-for="tag in uploadFormTags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="来源URL">
          <el-input v-model="uploadForm.source_url" placeholder="请输入来源URL（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="saving">上传</el-button>
      </template>
    </el-dialog>

    <!-- 编辑素材弹窗 -->
    <el-dialog v-model="showEditDialog" title="编辑素材" width="650px">
      <el-form :model="editForm" label-width="100px" :rules="editFormRules" ref="editFormRef">
        <el-form-item label="素材标题" prop="title">
          <el-input v-model="editForm.title" placeholder="请输入素材标题" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="素材内容" prop="content">
          <el-input v-model="editForm.content" type="textarea" :rows="4" placeholder="请输入素材内容（必填）" />
        </el-form-item>
        <el-form-item label="内容类型">
          <el-radio-group v-model="editForm.content_type">
            <el-radio value="text">纯文本</el-radio>
            <el-radio value="image_text">图文</el-radio>
          </el-radio-group>
        </el-form-item>
        <!-- 图文类型时显示图片管理 -->
        <el-form-item v-if="editForm.content_type === 'image_text'" label="素材图片">
          <div class="image-upload-area">
            <div v-for="(img, index) in editForm.images" :key="index" class="image-preview-item">
              <el-image :src="img.url" fit="cover" class="preview-img" />
              <el-icon class="remove-icon" @click="removeEditImage(index)"><Close /></el-icon>
            </div>
            <el-upload
              :show-file-list="false"
              :before-upload="beforeEditImageUpload"
              accept="image/*"
              class="image-uploader"
            >
              <div class="upload-placeholder">
                <el-icon><Plus /></el-icon>
                <span>添加图片</span>
              </div>
            </el-upload>
          </div>
        </el-form-item>
        <el-form-item label="素材话题" prop="topic">
          <el-input v-model="editForm.topic" placeholder="请输入素材话题（必选）" maxlength="255" />
        </el-form-item>
        <el-form-item label="所属平台" prop="platform_id">
          <el-select v-model="editForm.platform_id" placeholder="请选择平台" clearable style="width: 100%;" @change="handleEditPlatformChange">
            <el-option
              v-for="platform in getAllPlatforms()"
              :key="platform.id"
              :label="platform.name"
              :value="platform.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属分类" prop="category_id">
          <el-select v-model="editForm.category_id" placeholder="请先选择平台" clearable style="width: 100%;" @change="handleEditCategoryChange" :disabled="!editForm.platform_id">
            <el-option
              v-for="category in editFormCategories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属标签" prop="tags_ids">
          <el-select v-model="editForm.tag_ids" multiple placeholder="请先选择分类" style="width: 100%;" clearable :disabled="!editForm.category_id">
            <el-option
              v-for="tag in editFormTags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
          <div v-if="editForm.tag_ids.length === 0 && editForm.category_id" class="no-tag-hint">
            <el-tag type="info" size="small">无标签</el-tag>
          </div>
        </el-form-item>
        <el-form-item label="来源URL">
          <el-input v-model="editForm.source_url" placeholder="请输入来源URL（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 删除分类/标签确认弹窗 -->
    <el-dialog v-model="showTagDeleteDialog" title="删除确认" width="450px">
      <div v-if="deletingTag" class="delete-tag-content">
        <p v-if="deleteType === 'category'">确定要删除分类 <strong>{{ deletingTag.name }}</strong> 吗？</p>
        <p v-else>确定要删除标签 <strong>{{ deletingTag.name }}</strong> 吗？</p>

        <!-- 分类删除：检查标签和素材 -->
        <template v-if="deleteType === 'category'">
          <el-alert
            v-if="deletingTag.tagCount && deletingTag.tagCount > 0"
            :title="`该分类下有 ${deletingTag.tagCount} 个标签，请先删除所有标签`"
            type="warning"
            :closable="false"
            class="mt-md"
          />
          <el-alert
            v-else-if="deletingTag.material_count && deletingTag.material_count > 0"
            :title="`该分类下有 ${deletingTag.material_count} 个素材关联，请先迁移或删除素材`"
            type="warning"
            :closable="false"
            class="mt-md"
          />
          <el-alert
            v-else
            title="该分类下无标签和素材，可以安全删除"
            type="success"
            :closable="false"
            class="mt-md"
          />
        </template>

        <!-- 标签删除：检查素材 -->
        <template v-else-if="deleteType === 'tag'">
          <!-- 超级管理员：仅提示，不提供迁移选项 -->
          <template v-if="isSuperAdmin">
            <el-alert
              v-if="tagStats && tagStats.material_count > 0"
              :title="`该标签下有 ${tagStats.material_count} 个素材，请先迁移或删除所有素材后再删除标签`"
              type="warning"
              :closable="false"
              class="mt-md"
            />
            <el-alert
              v-else
              title="该标签下无素材，可以安全删除"
              type="success"
              :closable="false"
              class="mt-md"
            />
          </template>
          <!-- 创作管理员：提供迁移选项 -->
          <template v-else>
            <el-alert
              v-if="tagStats && tagStats.material_count > 0"
              :title="`该标签下有 ${tagStats.material_count} 个素材，请先选择目标标签进行迁移`"
              type="warning"
              :closable="false"
              class="mt-md"
            />
            <el-alert
              v-else
              title="该标签下无素材，可以安全删除"
              type="success"
              :closable="false"
              class="mt-md"
            />
            <div v-if="tagStats && tagStats.material_count > 0" class="mt-md">
              <el-form label-width="100px">
                <el-form-item label="目标标签" required>
                  <el-select v-model="targetMigrateTagId" placeholder="选择迁移目标标签" style="width: 100%;">
                    <el-option
                      v-for="tag in availableMigrateTags"
                      :key="tag.id"
                      :label="tag.name"
                      :value="tag.id"
                    />
                  </el-select>
                </el-form-item>
              </el-form>
            </div>
          </template>
        </template>
      </div>
      <template #footer>
        <el-button @click="showTagDeleteDialog = false">取消</el-button>
        <!-- 创作管理员删除标签时：有素材显示迁移并删除 -->
        <el-button
          v-if="deleteType === 'tag' && tagStats && tagStats.material_count > 0 && !isSuperAdmin"
          type="primary"
          @click="handleMigrateAndDeleteTag"
          :loading="saving"
          :disabled="!targetMigrateTagId"
        >
          迁移并删除
        </el-button>
        <!-- 确认删除按钮 -->
        <el-button
          type="danger"
          @click="handleConfirmDelete"
          :loading="saving"
          :disabled="(deleteType === 'category' && (deletingTag?.tagCount > 0 || deletingTag?.material_count > 0)) || (deleteType === 'tag' && isSuperAdmin && tagStats?.material_count > 0)"
        >
          确认删除
        </el-button>
      </template>
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
    <el-dialog v-model="showBatchCopyDialog" :title="isSuperAdmin ? '批量复制素材' : '批量复制素材'" width="550px">
      <div class="batch-copy-content">
        <p>已选择 <strong>{{ selectedIds.length }}</strong> 个素材，将复制为副本</p>
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

    <!-- 复制素材弹窗 -->
    <el-dialog v-model="showCopyDialog" title="复制素材" width="550px">
      <div class="copy-dialog-content">
        <p v-if="copyingMaterial">正在复制: <strong>{{ copyingMaterial.title }}</strong></p>
        <el-form label-width="100px" class="mt-md">
          <!-- 超级管理员：选择目标管理员 -->
          <el-form-item v-if="isSuperAdmin" label="目标管理员" required>
            <el-select v-model="copyTargetAdminId" placeholder="选择目标管理员" style="width: 100%;" @change="handleCopyAdminChange">
              <el-option
                v-for="op in operators"
                :key="op.id"
                :label="op.nickname || op.userid"
                :value="op.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="新标题" required>
            <el-input v-model="copyNewTitle" placeholder="请输入新标题" />
          </el-form-item>

          <!-- 超级管理员：选择目标平台 -->
          <el-form-item v-if="isSuperAdmin" label="目标平台" required>
            <el-select v-model="copyTargetPlatformId" placeholder="请先选择目标管理员" style="width: 100%;" :disabled="!copyTargetAdminId" @change="handleCopyPlatformChange">
              <el-option
                v-for="platform in copyTargetPlatforms"
                :key="platform.id"
                :label="platform.name"
                :value="platform.id"
              />
            </el-select>
          </el-form-item>

          <!-- 超级管理员：选择目标分类 -->
          <el-form-item v-if="isSuperAdmin" label="目标分类" required>
            <el-select v-model="copyTargetCategoryId" placeholder="请先选择目标平台" style="width: 100%;" :disabled="!copyTargetPlatformId" @change="handleCopyCategoryChange">
              <el-option
                v-for="category in copyTargetCategories"
                :key="category.id"
                :label="category.name"
                :value="category.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="目标标签" required>
            <el-select
              v-model="copyTargetTagIds"
              multiple
              placeholder="选择目标标签（可多选）"
              style="width: 100%;"
            >
              <!-- 超级管理员按分类显示标签 -->
              <template v-if="isSuperAdmin && copyTargetCategoryId">
                <el-option-group
                  v-for="group in copyTargetTagsGroupedByCategory"
                  :key="group.label"
                  :label="group.label"
                >
                  <el-option
                    v-for="tag in group.options"
                    :key="tag.id"
                    :label="tag.name"
                    :value="tag.id"
                  />
                </el-option-group>
              </template>
              <!-- 创作管理员按分类显示标签 -->
              <template v-else-if="!isSuperAdmin">
                <el-option-group
                  v-for="group in tagsGroupedByCategory"
                  :key="group.label"
                  :label="group.label"
                >
                  <el-option
                    v-for="tag in group.options"
                    :key="tag.id"
                    :label="tag.name"
                    :value="tag.id"
                  />
                </el-option-group>
              </template>
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showCopyDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmCopy"
          :loading="saving"
          :disabled="!copyNewTitle.trim() || copyTargetTagIds.length === 0 || (isSuperAdmin && (!copyTargetAdminId || !copyTargetPlatformId || !copyTargetCategoryId))"
        >
          确认复制
        </el-button>
      </template>
    </el-dialog>

    <!-- 管理素材标签弹窗 -->
    <el-dialog v-model="showManageTagsDialog" title="管理素材标签" width="500px">
      <div v-if="managingMaterial" class="manage-tags-content">
        <p class="mb-md">管理素材: <strong>{{ managingMaterial.title }}</strong></p>
        <el-form label-width="100px">
          <el-form-item label="当前标签">
            <div class="current-tags">
              <el-tag
                v-for="tag in managingMaterial.tags || []"
                :key="tag.id"
                closable
                size="small"
                class="mr-xs mb-xs"
                @close="handleRemoveMaterialTag(tag.id)"
              >
                {{ tag.name }}
              </el-tag>
              <span v-if="!managingMaterial.tags || managingMaterial.tags.length === 0" class="no-tags-text">暂无标签</span>
            </div>
          </el-form-item>
          <el-form-item label="添加标签">
            <el-select
              v-model="newMaterialTagIds"
              multiple
              placeholder="选择要添加的标签"
              style="width: 100%;"
            >
              <el-option
                v-for="tag in availableTagsForMaterial"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showManageTagsDialog = false">关闭</el-button>
        <el-button type="primary" @click="saveMaterialTags" :loading="saving">保存</el-button>
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
      <div v-if="previewMaterial" class="image-preview-content">
        <div class="preview-material-title mb-md">{{ previewMaterial.title }}</div>
        <div class="preview-image-list">
          <div
            v-for="(img, index) in previewImages"
            :key="index"
            class="preview-image-item"
          >
            <el-image
              :src="getFullImageUrl(img.file_url)"
              fit="contain"
              class="preview-full-image"
              :preview-src-list="previewOriginalUrls"
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
              <el-button size="small" type="primary" @click="downloadImage(img)">
                <el-icon><Download /></el-icon> 下载原图
              </el-button>
              <span class="image-index">{{ index + 1 }} / {{ previewImages.length }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 素材详情弹窗 -->
    <el-dialog
      v-model="showDetailDialog"
      title="素材详情"
      width="750px"
      :close-on-click-modal="true"
      class="detail-dialog"
    >
      <div v-if="detailMaterial" class="material-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="素材标题" :span="2">{{ detailMaterial.title }}</el-descriptions-item>
          <el-descriptions-item label="内容类型">
            {{ detailMaterial.content_type === 'image_text' ? '图文' : detailMaterial.content_type === 'video_text' ? '视频' : '纯文本' }}
          </el-descriptions-item>
          <el-descriptions-item label="所属平台">
            {{ detailMaterial.platform?.name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="所属分类" :span="2">
            {{ detailMaterial.category?.name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <template v-if="detailMaterial.tags && detailMaterial.tags.length > 0">
              <el-tag v-for="tag in detailMaterial.tags" :key="tag.id" size="small" type="info" class="mr-xs">{{ tag.name }}</el-tag>
            </template>
            <template v-else>无标签</template>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="detailMaterial.status === 'available' ? 'success' : 'info'" size="small">
              {{ detailMaterial.status === 'available' ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(detailMaterial.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="素材正文" :span="2">
            <div class="detail-text-content">{{ detailMaterial.content || '无' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="素材话题" :span="2">
            {{ detailMaterial.topic || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="来源URL" :span="2">
            <a v-if="detailMaterial.source_url" :href="detailMaterial.source_url" target="_blank" class="detail-link">
              {{ detailMaterial.source_url }}
            </a>
            <span v-else class="detail-empty-text">无</span>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 图片信息 -->
        <div v-if="detailMaterial.content_type === 'image_text' && detailImages.length > 0" class="detail-section">
          <div class="detail-section-title">素材图片</div>
          <div class="detail-image-list">
            <div
              v-for="(img, index) in detailImages"
              :key="index"
              class="detail-image-item"
              @click="() => { previewMaterial = detailMaterial; showImagePreview = true; }"
            >
              <el-image
                :src="getFullImageUrl(img.thumbnail_url || img.file_url)"
                fit="cover"
                class="detail-image"
                :preview-src-list="detailOriginalUrls"
                :initial-index="index"
              >
                <template #error>
                  <div class="detail-image-placeholder">
                    <el-icon :size="24" color="#909399"><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <div class="detail-image-overlay">
                <el-icon :size="16"><View /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Document, Delete, Loading, Picture, PriceTag, Close, View, Download, Folder, Tickets } from '@element-plus/icons-vue'
import { apiClient, type Material, type MaterialTag, type MaterialCategory, type CategoryTreePlatform, type User, type MaterialTagSummary, type OperationLogCreateParams } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

// 操作日志模块常量
const MODULE_MATERIALS = 'materials'

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

const searchKeyword = ref('')
const searchType = ref('')
const searchStatus = ref('')
const viewMode = ref('card')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const showUploadDialog = ref(false)
const showEditDialog = ref(false)
const showPlatformDialog = ref(false)
const showCategoryDialog = ref(false)
const showTagDialog = ref(false)
const showTagDeleteDialog = ref(false)
const showBatchMigrateDialog = ref(false)
const showBatchCopyDialog = ref(false)
const showCopyDialog = ref(false)
const showManageTagsDialog = ref(false)
const showImagePreview = ref(false)
const previewMaterial = ref<Material | null>(null)
const showDetailDialog = ref(false)
const detailMaterial = ref<Material | null>(null)
const deleteType = ref<'category' | 'tag'>('tag')

// 超级管理员：选中的管理员筛选
const selectedAdminId = ref<number | null>(null)
const treeSelectedAdminId = ref<number | null>(null) // 树节点选择的管理员（不影响下拉框）

// 标签删除相关
const deletingTag = ref<MaterialTag | null>(null)
const tagStats = ref<{ material_count: number; material_ids: number[] } | null>(null)
const targetMigrateTagId = ref<number | null>(null)

// 批量迁移相关（支持多选标签）
const batchMigrateTargetTagIds = ref<number[]>([])
const batchMigrateTargetAdminId = ref<number | null>(null)
const batchMigrateTargetPlatformId = ref<number | null>(null)
const batchMigrateTargetCategoryId = ref<number | null>(null)

// 批量复制相关
const batchCopyTargetAdminId = ref<number | null>(null)
const batchCopyTargetPlatformId = ref<number | null>(null)
const batchCopyTargetCategoryId = ref<number | null>(null)
const batchCopyTargetTagIds = ref<number[]>([])

// 复制素材相关
const copyingMaterial = ref<Material | null>(null)
const copyTargetAdminId = ref<number | null>(null)
const copyTargetPlatformId = ref<number | null>(null)
const copyTargetCategoryId = ref<number | null>(null)
const copyNewTitle = ref('')
const copyTargetTagIds = ref<number[]>([])

// 管理标签相关
const managingMaterial = ref<Material | null>(null)
const newMaterialTagIds = ref<number[]>([])
const removedMaterialTagIds = ref<number[]>([])

// 列表视图批量操作
const selectedIds = ref<number[]>([])

// 删除平台相关
const showDeletePlatformDialog = ref(false)
const deletingPlatform = ref<any>(null)
const deletingPlatformLoading = ref(false)

// 素材列表
const materialList = ref<Material[]>([])

// 分类树数据（按管理员分组）
const categoryTreeData = ref<{ adminId?: number; adminName?: string; platforms?: any[]; id?: number; name?: string; color?: string; material_count?: number; category_count?: number; categories?: any[] }[]>([])

// 标签统计摘要
const tagSummary = ref<MaterialTagSummary | null>(null)

// 创作管理员列表（超级管理员用）
const operators = ref<User[]>([])

// 树形配置
const categoryTreeProps = {
  label: 'name',
  children: 'children'
}

// 构建平台/分类/标签节点
function buildPlatformNode(platform: any) {
  const platformNode = {
    key: `platform_${platform.id}`,
    id: platform.id,
    name: platform.name,
    type: 'platform',
    color: platform.color,
    count: platform.material_count ?? 0,
    material_count: platform.material_count ?? 0,
    category_count: platform.category_count ?? 0,
    isSystem: false,
    children: [] as any[]
  }

  platform.categories?.forEach((category: any) => {
    const categoryNode = {
      key: `category_${category.id}`,
      id: category.id,
      name: category.name,
      type: 'category',
      color: category.color,
      platformId: platform.id,
      count: category.material_count ?? 0,
      tagCount: category.tags?.length ?? 0,
      material_count: category.material_count ?? 0,
      isSystem: false,
      children: [] as any[]
    }

    // 添加标签节点
    category.tags?.forEach((tag: any) => {
      categoryNode.children.push({
        key: `tag_${tag.id}`,
        id: tag.id,
        name: tag.name,
        type: 'tag',
        color: tag.color,
        categoryId: category.id,
        platformId: platform.id,
        count: tag.material_count ?? 0,
        isSystem: tag.is_system ?? false,
        children: []
      })
    })

    platformNode.children.push(categoryNode)
  })

  return platformNode
}

// 构建树形结构
const categoryTree = computed(() => {
  const nodes: any[] = [{
    key: 'all',
    name: '全部分类标签',
    type: 'all',
    isSystem: true,
    children: []
  }]

  // 判断当前是否为分组模式：超级管理员且未通过下拉框选择管理员
  // 注意：树节点选择的 admin（treeSelectedAdminId）不影响树形显示
  const isGroupedMode = isSuperAdmin.value &&
                        selectedAdminId.value === null &&
                        categoryTreeData.value.length > 0 &&
                        categoryTreeData.value[0]?.adminId !== undefined

  if (isGroupedMode) {
    // 按管理员分组显示
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
    // 普通模式：直接显示平台
    categoryTreeData.value.forEach(platform => {
      if (platform.id && platform.name) {
        nodes.push(buildPlatformNode(platform))
      }
    })
  }

  return nodes
})

// 可用于迁移的标签列表（排除当前要删除的标签）
const availableMigrateTags = computed(() => {
  // 从所有分类树数据中收集当前分类下的其他标签
  if (deletingTag.value && deleteType.value === 'tag') {
    const allTags: MaterialTag[] = []
    const allPlatforms = getAllPlatforms()
    allPlatforms.forEach(platform => {
      platform.categories?.forEach(category => {
        category.tags?.forEach(tag => {
          if (tag.id !== deletingTag.value!.id) {
            allTags.push(tag as unknown as MaterialTag)
          }
        })
      })
    })
    return allTags
  }
  return []
})

// 从树数据中提取所有分类（用于表单选择）
const availableCategories = computed(() => {
  const categories: { id: number; name: string; platformId: number; platformName: string }[] = []

  // 处理按管理员分组的数据结构
  categoryTreeData.value.forEach(item => {
    if (item.platforms) {
      // 按管理员分组的结构
      item.platforms.forEach(platform => {
        platform.categories?.forEach(category => {
          categories.push({
            id: category.id,
            name: category.name,
            platformId: platform.id,
            platformName: platform.name
          })
        })
      })
    } else if (item.id && item.name) {
      // 普通的平台结构
      const platform = item as any
      platform.categories?.forEach(category => {
        categories.push({
          id: category.id,
          name: category.name,
          platformId: platform.id,
          platformName: platform.name
        })
      })
    }
  })
  return categories
})

// 获取所有平台列表（扁平化）
function getAllPlatforms() {
  const platforms: any[] = []
  categoryTreeData.value.forEach(item => {
    if (item.platforms) {
      // 按管理员分组的结构
      item.platforms.forEach(p => platforms.push(p))
    } else if (item.id && item.name) {
      // 普通的平台结构
      platforms.push(item)
    }
  })
  return platforms
}

// 根据平台ID获取平台名称
function getPlatformName(platformId: number | undefined): string {
  if (!platformId) return '-'
  const platforms = getAllPlatforms()
  const platform = platforms.find(p => p.id === platformId)
  return platform?.name || '-'
}

// 根据分类ID获取分类名称
function getCategoryName(categoryId: number | undefined): string {
  if (!categoryId) return '-'
  // 从 categoryTreeData 中查找分类
  for (const item of categoryTreeData.value) {
    // 检查是否是平台节点
    if (item.platforms) {
      for (const platform of item.platforms) {
        if (platform.categories) {
          const category = platform.categories.find((c: any) => c.id === categoryId)
          if (category) return category.name
        }
      }
    }
    // 检查是否是顶层分类
    if (item.categories) {
      const category = item.categories.find((c: any) => c.id === categoryId)
      if (category) return category.name
    }
  }
  return '-'
}

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

// 上传表单：根据选择的平台过滤分类
const uploadFormCategories = computed(() => {
  if (!uploadForm.platform_id) return []
  const allPlatforms = getAllPlatforms()
  const platform = allPlatforms.find(p => p.id === uploadForm.platform_id)
  return platform?.categories?.map(c => ({
    id: c.id,
    name: c.name,
    platformId: platform.id
  })) || []
})

// 上传表单：根据选择的分类过滤标签
const uploadFormTags = computed(() => {
  if (!uploadForm.category_id) return []
  const allPlatforms = getAllPlatforms()
  for (const platform of allPlatforms) {
    for (const category of (platform.categories || [])) {
      if (category.id === uploadForm.category_id) {
        return category.tags?.map(t => ({
          id: t.id,
          name: t.name
        })) || []
      }
    }
  }
  return []
})

// 编辑表单：根据选择的平台过滤分类
const editFormCategories = computed(() => {
  if (!editForm.platform_id) return []
  const allPlatforms = getAllPlatforms()
  const platform = allPlatforms.find(p => p.id === editForm.platform_id)
  return platform?.categories?.map(c => ({
    id: c.id,
    name: c.name,
    platformId: platform.id
  })) || []
})

// 编辑表单：根据选择的分类过滤标签
const editFormTags = computed(() => {
  if (!editForm.category_id) return []
  const allPlatforms = getAllPlatforms()
  for (const platform of allPlatforms) {
    for (const category of (platform.categories || [])) {
      if (category.id === editForm.category_id) {
        return category.tags?.map(t => ({
          id: t.id,
          name: t.name
        })) || []
      }
    }
  }
  return []
})

// 从树数据中提取所有标签
const tags = computed<MaterialTag[]>(() => {
  const allTags: MaterialTag[] = []
  const allPlatforms = getAllPlatforms()
  allPlatforms.forEach(platform => {
    platform.categories?.forEach(category => {
      category.tags?.forEach(tag => {
        allTags.push(tag as unknown as MaterialTag)
      })
    })
  })
  return allTags
})

// 根据分类ID获取可用的标签（用于表单中的标签选择）
function availableTagsForForm(categoryId?: number | null): MaterialTag[] {
  if (!categoryId) return []
  const allTags: MaterialTag[] = []
  const allPlatforms = getAllPlatforms()
  allPlatforms.forEach(platform => {
    platform.categories?.forEach(category => {
      if (category.id === categoryId) {
        category.tags?.forEach(tag => {
          allTags.push(tag as unknown as MaterialTag)
        })
      }
    })
  })
  return allTags
}

// 标签按分类分组（用于弹窗中的分组选择）
const tagsGroupedByCategory = computed(() => {
  const groups: { label: string; options: MaterialTag[] }[] = []
  const allPlatforms = getAllPlatforms()
  allPlatforms.forEach(platform => {
    platform.categories?.forEach(category => {
      const categoryTags: MaterialTag[] = []
      category.tags?.forEach(tag => {
        categoryTags.push(tag as unknown as MaterialTag)
      })
      if (categoryTags.length > 0) {
        groups.push({
          label: `${platform.name} / ${category.name}`,
          options: categoryTags
        })
      }
    })
  })
  return groups
})

// 从指定标签列表按分类分组（超级管理员用）
function groupTagsByCategory(tagsList: MaterialTag[]) {
  const tagMap = new Map<number, MaterialTag>()
  tagsList.forEach(t => tagMap.set(t.id, t))

  const groups: { label: string; options: MaterialTag[] }[] = []
  const allPlatforms = getAllPlatforms()
  allPlatforms.forEach(platform => {
    platform.categories?.forEach(category => {
      const categoryTags: MaterialTag[] = []
      category.tags?.forEach(tag => {
        if (tagMap.has(tag.id)) {
          categoryTags.push(tag as unknown as MaterialTag)
        }
      })
      if (categoryTags.length > 0) {
        groups.push({
          label: `${platform.name} / ${category.name}`,
          options: categoryTags
        })
      }
    })
  })
  return groups
}

// 复制功能：目标管理员的平台列表
const copyTargetPlatforms = computed(() => {
  if (!copyTargetAdminId.value) return []
  // 从 categoryTreeData 中查找该管理员的平台
  const adminTree = categoryTreeData.value.find(item => item.adminId === copyTargetAdminId.value)
  return adminTree?.platforms || []
})

// 复制功能：目标平台下的分类列表
const copyTargetCategories = computed(() => {
  if (!copyTargetPlatformId.value) return []
  const platform = copyTargetPlatforms.value.find(p => p.id === copyTargetPlatformId.value)
  return platform?.categories || []
})

// 复制功能：目标分类下的标签按分类分组
const copyTargetTagsGroupedByCategory = computed(() => {
  if (!copyTargetCategoryId.value) return []
  const categories = copyTargetCategories.value.filter(c => c.id === copyTargetCategoryId.value)
  return categories.map(category => ({
    label: category.name,
    options: (category.tags || []).map((tag: any) => ({
      id: tag.id,
      name: tag.name
    }))
  }))
})

// 复制功能：当前选择的管理员对应的标签列表（保留兼容）
const tagsForCopyAdmin = computed(() => {
  if (!copyTargetAdminId.value) return []
  return copyAvailableTags.value.filter(tag => tag.owner_admin_id === copyTargetAdminId.value)
})

// 复制对话框：目标管理员的所有可用标签（独立加载）
const copyAvailableTags = ref<MaterialTag[]>([])

// 管理标签弹窗：可添加的标签（排除已关联的标签）
const availableTagsForMaterial = computed(() => {
  if (!managingMaterial.value) return tags.value
  const currentTagIds = new Set((managingMaterial.value.tags || []).map(t => t.id))
  return tags.value.filter(tag => !currentTagIds.has(tag.id))
})

// 批量迁移：当前选择的目标管理员对应的标签列表（超级管理员用）
const tagsForBatchMigrateAdmin = computed(() => {
  if (!batchMigrateTargetAdminId.value) return []
  return batchMigrateAvailableTags.value.filter(tag => tag.owner_admin_id === batchMigrateTargetAdminId.value)
})

// 批量迁移对话框：目标管理员的所有可用标签（独立加载）
const batchMigrateAvailableTags = ref<MaterialTag[]>([])

// 批量复制用：可用平台列表
const platformsForBatchCopy = computed(() => {
  if (isSuperAdmin.value) {
    return getAdminPlatforms(batchCopyTargetAdminId.value)
  }
  // 创作管理员直接使用当前用户的平台
  return getAllPlatforms()
})

// 批量迁移用：可用平台列表
const platformsForBatchMigrate = computed(() => {
  if (isSuperAdmin.value) {
    return getAdminPlatforms(batchMigrateTargetAdminId.value)
  }
  return getAllPlatforms()
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

// 当前选中的节点
const selectedTagId = ref<number | string>('all')
const selectedPlatformId = ref<number | null>(null)
const selectedCategoryId = ref<number | null>(null)

// 表单
const platformForm = reactive({
  name: '',
  description: '',
  color: '#8B7CF6'
})

const categoryForm = reactive({
  name: '',
  description: '',
  color: '#67C23A',
  platformId: 0,
  platformName: ''
})

const tagForm = reactive({
  name: '',
  description: '',
  color: '#909399',
  category_id: 0,
  categoryName: ''
})

const uploadForm = reactive({
  title: '',
  content: '',
  topic: '',
  content_type: 'image_text' as 'text' | 'image_text' | 'video',
  text_content: '',
  platform_id: undefined as number | undefined,
  category_id: undefined as number | undefined,
  tag_ids: [] as number[],
  source_url: '',
  images: [] as { url: string; file?: File }[]
})

const editForm = reactive({
  id: 0,
  title: '',
  content: '',
  topic: '',
  content_type: 'image_text' as 'text' | 'image_text' | 'video',
  text_content: '',
  platform_id: undefined as number | undefined,
  category_id: undefined as number | undefined,
  tag_ids: [] as number[],
  source_url: '',
  images: [] as { url: string; file?: File; id?: number }[]
})

// 跟踪要删除的附件ID
const deletedAttachmentIds = ref<number[]>([])

// 表单验证规则
const uploadFormRules = {
  title: [{ required: true, message: '请输入素材标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入素材内容', trigger: 'blur' }],
  topic: [{ required: true, message: '请输入素材话题', trigger: 'blur' }],
  platform_id: [{ required: true, message: '请选择所属平台', trigger: 'change' }],
  category_id: [{ required: true, message: '请选择所属分类', trigger: 'change' }],
  tag_ids: [{ required: true, message: '请选择所属标签', trigger: 'change', type: 'array' as const, min: 1 }]
}

const editFormRules = {
  title: [{ required: true, message: '请输入素材标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入素材内容', trigger: 'blur' }],
  topic: [{ required: true, message: '请输入素材话题', trigger: 'blur' }],
  platform_id: [{ required: true, message: '请选择所属平台', trigger: 'change' }],
  category_id: [{ required: true, message: '请选择所属分类', trigger: 'change' }],
  tag_ids: [{ required: true, message: '请选择所属标签', trigger: 'change', type: 'array' as const, min: 1 }]
}

// 表单引用
const uploadFormRef = ref()
const editFormRef = ref()

// 获取素材列表
async function fetchMaterials() {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      limit: pageSize.value
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (searchType.value) params.content_type = searchType.value
    if (searchStatus.value) params.status = searchStatus.value

    // 标签筛选：通过节点类型判断筛选条件
    const nodeKey = String(selectedTagId.value)
    if (nodeKey.startsWith('tag_')) {
      // 选中了某个标签
      params.tag_id = nodeKey.replace('tag_', '')
    } else if (nodeKey.startsWith('category_')) {
      // 选中了某个分类（显示该分类下所有标签的素材）
      params.category_id = nodeKey.replace('category_', '')
    } else if (nodeKey.startsWith('platform_')) {
      // 选中了某个平台（显示该平台下所有素材）
      params.platform_id = nodeKey.replace('platform_', '')
    }

    // 管理员筛选（超级管理员）：优先使用树节点选择的管理员，否则使用下拉框选择的管理员
    if (isSuperAdmin.value) {
      const effectiveAdminId = treeSelectedAdminId.value !== null ? treeSelectedAdminId.value : selectedAdminId.value
      if (effectiveAdminId !== null) {
        if (effectiveAdminId === 0) {
          // 超级管理员创建的素材 - owner_operator_id 传 null
          params.owner_operator_id = null
        } else {
          params.owner_operator_id = effectiveAdminId
        }
      }
    }

    const result = await apiClient.getMaterials(params)
    console.log('[MaterialList] fetchMaterials received result.items:', result.items)
    if (result.items && result.items.length > 0) {
      console.log('[MaterialList] First item:', result.items[0])
      console.log('[MaterialList] First item.platform:', result.items[0].platform)
      console.log('[MaterialList] First item.category:', result.items[0].category)
      console.log('[MaterialList] First item.tags:', result.items[0].tags)
    }
    materialList.value = result.items
    total.value = result.total
  } catch (error: any) {
    ElMessage.error(error.message || '获取素材列表失败')
  } finally {
    loading.value = false
  }
}

// 获取分类树数据
async function fetchCategoryTree() {
  try {
    // 超级管理员按选中的管理员筛选
    if (isSuperAdmin.value && selectedAdminId.value !== null) {
      if (selectedAdminId.value === 0) {
        // 超级管理员自己的素材
        categoryTreeData.value = []
        tagSummary.value = { total: 0, no_tag_count: 0, tag_counts: {} }
        return
      } else {
        // 选中了特定管理员
        const params = { owner_operator_id: selectedAdminId.value }
        const result = await apiClient.getMaterialPlatformTree(params)
        categoryTreeData.value = result.platforms.map((p: any) => ({ ...p }))
        tagSummary.value = {
          total: result.material_total,
          no_tag_count: 0,
          tag_counts: {}
        }
        return
      }
    }

    // 未选择管理员：获取所有管理员的平台树，按管理员分组
    if (isSuperAdmin.value && operators.value.length > 0) {
      const adminTrees: any[] = []
      let totalMaterials = 0

      for (const operator of operators.value) {
        try {
          const result = await apiClient.getMaterialPlatformTree({ owner_operator_id: operator.id })
          if (result.platforms && result.platforms.length > 0) {
            adminTrees.push({
              adminId: operator.id,
              adminName: operator.nickname || operator.userid,
              platforms: result.platforms
            })
            totalMaterials += result.material_total || 0
          }
        } catch (e) {
          console.warn(`获取管理员 ${operator.nickname} 的平台树失败:`, e)
        }
      }

      categoryTreeData.value = adminTrees
      tagSummary.value = {
        total: totalMaterials,
        no_tag_count: 0,
        tag_counts: {}
      }
    } else {
      // 非超级管理员：直接获取自己的平台树
      const result = await apiClient.getMaterialPlatformTree({})
      categoryTreeData.value = result.platforms.map((p: any) => ({ ...p }))
      tagSummary.value = {
        total: result.material_total,
        no_tag_count: 0,
        tag_counts: {}
      }
    }
  } catch (error: any) {
    console.error('获取分类树失败:', error)
  }
}

// 管理员筛选变更处理
function handleAdminChange() {
  // 清空树选择的管理员ID，因为下拉框选择优先
  treeSelectedAdminId.value = null
  selectedTagId.value = 'all'
  selectedCategoryId.value = null
  currentPage.value = 1
  fetchCategoryTree()
  fetchMaterials()
}

// 获取创作管理员列表（超级管理员用）
async function fetchOperators() {
  if (!isSuperAdmin.value) return
  try {
    console.log('[MaterialList] fetchOperators: 开始获取创作管理员列表')
    const result = await apiClient.getOperators({ limit: 100 })
    console.log('[MaterialList] fetchOperators: 获取到数据，items数量:', result.items?.length, 'total:', result.total)
    console.log('[MaterialList] fetchOperators: operators数据:', result.items?.map(o => ({ id: o.id, nickname: o.nickname, userid: o.userid })))
    operators.value = result.items
  } catch (error: any) {
    console.error('获取创作管理员列表失败:', error)
  }
}

// 初始化
onMounted(async () => {
  fetchMaterials()
  // 超级管理员需要先加载 operators 列表，再获取分类树
  if (isSuperAdmin.value) {
    await fetchOperators()
  }
  fetchCategoryTree()
})

// 工具函数
// API 基础 URL（不含 /api/v1 路径）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:8000'

function getTextSnippet(text?: string): string {
  if (!text) return ''
  return text.length > 50 ? text.substring(0, 50) + '...' : text
}

// 拼接完整的图片 URL
function getFullImageUrl(url: string | undefined): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${API_BASE_URL}${url}`
}

function getThumbnail(material: Material): string {
  if (material.attachments && material.attachments.length > 0) {
    const url = material.attachments[0].thumbnail_url || material.attachments[0].file_url
    return getFullImageUrl(url)
  }
  return ''
}

function getImageCount(material: Material): number {
  if (material.attachments) {
    return material.attachments.filter(a => a.file_type === 'image').length
  }
  return material.image_count || 0
}

const previewImages = computed(() => {
  if (!previewMaterial.value) return []
  return (previewMaterial.value.attachments || []).filter(a => a.file_type === 'image')
})

const previewOriginalUrls = computed(() => {
  return previewImages.value.map(img => getFullImageUrl(img.file_url))
})

function handlePreviewImages(material: Material) {
  previewMaterial.value = material
  showImagePreview.value = true
}

function handleViewDetail(material: Material) {
  console.log('[MaterialList] handleViewDetail called with material:', material)
  console.log('[MaterialList] material.platform:', material.platform)
  console.log('[MaterialList] material.category:', material.category)
  console.log('[MaterialList] material.tags:', material.tags)
  detailMaterial.value = material
  showDetailDialog.value = true
}

const detailImages = computed(() => {
  if (!detailMaterial.value) return []
  return (detailMaterial.value.attachments || []).filter(a => a.file_type === 'image')
})

const detailOriginalUrls = computed(() => {
  return detailImages.value.map(img => getFullImageUrl(img.file_url))
})

function downloadImage(attachment: { file_url: string; file_name?: string }) {
  const link = document.createElement('a')
  link.href = getFullImageUrl(attachment.file_url)
  link.download = attachment.file_name || 'image.jpg'
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function getContentTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    'text': '纯文本',
    'image_text': '图文',
    'video': '视频',
    'mix': '混合'
  }
  return labels[type] || type
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

function getOperatorName(ownerId: number | undefined): string {
  if (ownerId === undefined || ownerId === null) {
    return '未知'
  }
  const op = operators.value.find(o => o.id === ownerId)
  if (!op) {
    console.warn(`[MaterialList] Operator not found for ownerId: ${ownerId}, available operators:`, operators.value.map(o => ({ id: o.id, nickname: o.nickname, userid: o.userid })))
    return `管理员${ownerId}`
  }
  return op.nickname || op.userid || `管理员${ownerId}`
}

// 事件处理 - 树节点点击
function handleNodeClick(data: any) {
  selectedTagId.value = data.key
  if (data.type === 'all') {
    // 重置所有筛选条件，包括树选择的管理员
    treeSelectedAdminId.value = null
    selectedCategoryId.value = null
    selectedPlatformId.value = null
    currentPage.value = 1
    fetchMaterials()
  } else if (data.type === 'admin') {
    // 点击管理员节点：设置树选择的管理员用于筛选数据，但保持显示全部树形
    treeSelectedAdminId.value = data.id
    // 不清空 selectedAdminId（下拉框保持不变）
    // 不调用 fetchCategoryTree()，保持树形列表不变
    selectedPlatformId.value = null
    selectedCategoryId.value = null
    currentPage.value = 1
    // 仅刷新素材列表（使用该管理员筛选）
    fetchMaterials()
  } else if (data.type === 'platform') {
    // 点击平台：显示该平台下所有素材
    selectedPlatformId.value = data.id
    selectedCategoryId.value = null
    currentPage.value = 1
    fetchMaterialsByPlatform(data.id)
  } else if (data.type === 'category') {
    selectedPlatformId.value = data.platformId
    selectedCategoryId.value = data.id
    currentPage.value = 1
    // 获取该分类下所有素材（包括所有标签）
    fetchMaterialsByCategory(data.id)
  } else if (data.type === 'tag') {
    selectedPlatformId.value = data.platformId
    selectedCategoryId.value = data.categoryId
    currentPage.value = 1
    // 筛选特定标签的素材
    fetchMaterialsByTag(data.id)
  }
}

// 根据平台获取素材
async function fetchMaterialsByPlatform(platformId: number) {
  loading.value = true
  try {
    const params: any = {
      page: 1,
      limit: pageSize.value,
      platform_id: platformId
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (searchType.value) params.content_type = searchType.value
    if (searchStatus.value) params.status = searchStatus.value

    // 管理员筛选：优先使用树节点选择的管理员，否则使用下拉框选择的管理员
    if (isSuperAdmin.value) {
      const effectiveAdminId = treeSelectedAdminId.value !== null ? treeSelectedAdminId.value : selectedAdminId.value
      if (effectiveAdminId !== null) {
        params.owner_operator_id = effectiveAdminId === 0 ? null : effectiveAdminId
      }
    }

    const result = await apiClient.getMaterials(params)
    materialList.value = result.items
    total.value = result.total
  } catch (error: any) {
    ElMessage.error(error.message || '获取素材列表失败')
  } finally {
    loading.value = false
  }
}

// 根据分类获取素材
async function fetchMaterialsByCategory(categoryId: number) {
  loading.value = true
  try {
    const params: any = {
      page: 1,
      limit: pageSize.value,
      category_id: categoryId
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (searchType.value) params.content_type = searchType.value
    if (searchStatus.value) params.status = searchStatus.value

    // 管理员筛选：优先使用树节点选择的管理员，否则使用下拉框选择的管理员
    if (isSuperAdmin.value) {
      const effectiveAdminId = treeSelectedAdminId.value !== null ? treeSelectedAdminId.value : selectedAdminId.value
      if (effectiveAdminId !== null) {
        params.owner_operator_id = effectiveAdminId === 0 ? null : effectiveAdminId
      }
    }

    const result = await apiClient.getMaterials(params)
    materialList.value = result.items
    total.value = result.total
  } catch (error: any) {
    ElMessage.error(error.message || '获取素材列表失败')
  } finally {
    loading.value = false
  }
}

// 根据分类获取无标签素材
async function fetchMaterialsByCategoryNoTag(categoryId: number) {
  loading.value = true
  try {
    const params: any = {
      page: 1,
      limit: pageSize.value,
      category_id: categoryId,
      no_tag: true
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (searchType.value) params.content_type = searchType.value
    if (searchStatus.value) params.status = searchStatus.value

    // 管理员筛选：优先使用树节点选择的管理员，否则使用下拉框选择的管理员
    if (isSuperAdmin.value) {
      const effectiveAdminId = treeSelectedAdminId.value !== null ? treeSelectedAdminId.value : selectedAdminId.value
      if (effectiveAdminId !== null) {
        params.owner_operator_id = effectiveAdminId === 0 ? null : effectiveAdminId
      }
    }

    const result = await apiClient.getMaterials(params)
    materialList.value = result.items
    total.value = result.total
  } catch (error: any) {
    ElMessage.error(error.message || '获取素材列表失败')
  } finally {
    loading.value = false
  }
}

// 根据标签获取素材
async function fetchMaterialsByTag(tagId: number) {
  loading.value = true
  try {
    const params: any = {
      page: 1,
      limit: pageSize.value,
      tag_id: tagId
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (searchType.value) params.content_type = searchType.value
    if (searchStatus.value) params.status = searchStatus.value

    // 管理员筛选：优先使用树节点选择的管理员，否则使用下拉框选择的管理员
    if (isSuperAdmin.value) {
      const effectiveAdminId = treeSelectedAdminId.value !== null ? treeSelectedAdminId.value : selectedAdminId.value
      if (effectiveAdminId !== null) {
        params.owner_operator_id = effectiveAdminId === 0 ? null : effectiveAdminId
      }
    }

    const result = await apiClient.getMaterials(params)
    materialList.value = result.items
    total.value = result.total
  } catch (error: any) {
    ElMessage.error(error.message || '获取素材列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchMaterials()
}

// 上传表单：平台变更时重置分类和标签
function handleUploadPlatformChange() {
  uploadForm.category_id = undefined
  uploadForm.tag_ids = []
}

// 编辑表单：平台变更时重置分类和标签
function handleEditPlatformChange() {
  editForm.category_id = undefined
  editForm.tag_ids = []
}

// 编辑表单：分类变更时重置标签
function handleEditCategoryChange() {
  editForm.tag_ids = []
}

// 添加平台
function handleAddPlatform() {
  platformForm.name = ''
  platformForm.description = ''
  platformForm.color = '#2563EB'
  showPlatformDialog.value = true
}

// 删除平台
async function handleDeletePlatform(data: any) {
  deletingPlatform.value = data
  // 查询平台下的素材数量
  try {
    const stats = await apiClient.getMaterialPlatformStats(data.id)
    deletingPlatform.value = { ...data, material_count: stats.material_count || 0 }
  } catch (error: any) {
    console.error('获取平台统计失败:', error)
    deletingPlatform.value = { ...data, material_count: 0 }
  }
  showDeletePlatformDialog.value = true
}

async function confirmDeletePlatform() {
  if (!deletingPlatform.value) return
  if (deletingPlatform.value.material_count > 0) {
    ElMessage.warning('请先迁移或删除平台下的所有素材')
    return
  }

  deletingPlatformLoading.value = true
  try {
    await apiClient.deleteMaterialPlatform(deletingPlatform.value.id)
    ElMessage.success('平台删除成功')
    showDeletePlatformDialog.value = false
    deletingPlatform.value = null
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '删除平台失败')
  } finally {
    deletingPlatformLoading.value = false
  }
}

// 保存平台
async function handleSavePlatform() {
  if (!platformForm.name.trim()) {
    ElMessage.warning('请输入平台名称')
    return
  }
  saving.value = true
  try {
    await apiClient.createMaterialPlatform({
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
function handleAddCategory(platformData: any) {
  categoryForm.name = ''
  categoryForm.description = ''
  categoryForm.color = '#67C23A'
  categoryForm.platformId = platformData.id
  categoryForm.platformName = platformData.name
  showCategoryDialog.value = true
}

// 保存分类
async function handleSaveCategory() {
  if (!categoryForm.name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  saving.value = true
  try {
    await apiClient.createMaterialCategory({
      name: categoryForm.name,
      platform_id: categoryForm.platformId,
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

// 删除分类
async function handleRemoveCategory(data: any) {
  if (data.isSystem) {
    ElMessage.warning('系统默认分类不可删除')
    return
  }
  // 查询分类下的素材数量
  try {
    const stats = await apiClient.getMaterialCategoryStats(data.id)
    deletingTag.value = { ...data, material_count: stats.material_count || 0, tagCount: stats.tag_count || data.tagCount }
    deleteType.value = 'category'
    targetMigrateTagId.value = null
    showTagDeleteDialog.value = true
  } catch (error: any) {
    ElMessage.error(error.message || '获取分类信息失败')
  }
}

// 添加标签
function handleAddTag(categoryData: any) {
  tagForm.name = ''
  tagForm.description = ''
  tagForm.color = '#909399'
  tagForm.category_id = categoryData.id
  tagForm.categoryName = categoryData.name
  showTagDialog.value = true
}

// 保存标签
async function handleSaveTag() {
  if (!tagForm.name.trim()) {
    ElMessage.warning('请输入标签名称')
    return
  }
  if (!tagForm.category_id) {
    ElMessage.warning('请选择所属分类')
    return
  }
  saving.value = true
  try {
    await apiClient.createMaterialTag({
      name: tagForm.name,
      category_id: tagForm.category_id,
      description: tagForm.description || undefined,
      color: tagForm.color
    })
    ElMessage.success('标签创建成功')
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
  // 先查询标签下素材数量
  try {
    const stats = await apiClient.getMaterialTagStats(data.id)
    deletingTag.value = data
    deleteType.value = 'tag'
    tagStats.value = stats
    targetMigrateTagId.value = null
    showTagDeleteDialog.value = true
  } catch (error: any) {
    ElMessage.error(error.message || '获取标签信息失败')
  }
}

// 确认删除（分类或标签）
async function handleConfirmDelete() {
  if (!deletingTag.value) return

  // 分类删除：检查是否有标签或素材
  if (deleteType.value === 'category') {
    if (deletingTag.value.tagCount > 0) {
      ElMessage.warning('请先删除该分类下的所有标签')
      return
    }
    if (deletingTag.value.material_count > 0) {
      ElMessage.warning('请先迁移或删除该分类下的所有素材')
      return
    }
  }

  // 标签删除：超级管理员不允许迁移，只能删除无素材的标签
  if (deleteType.value === 'tag' && isSuperAdmin.value) {
    if (tagStats.value && tagStats.value.material_count > 0) {
      ElMessage.warning('该标签下有素材，请先迁移或删除所有素材后再删除标签')
      return
    }
  }

  saving.value = true
  try {
    if (deleteType.value === 'category') {
      await apiClient.deleteMaterialCategory(deletingTag.value.id)
      ElMessage.success('分类删除成功')
    } else {
      await apiClient.deleteMaterialTag(deletingTag.value.id)
      ElMessage.success('标签删除成功')
    }
    showTagDeleteDialog.value = false
    fetchCategoryTree()
    if (selectedTagId.value === deletingTag.value.id) {
      selectedTagId.value = 'all'
      fetchMaterials()
    }
    deletingTag.value = null
    tagStats.value = null
  } catch (error: any) {
    ElMessage.error(error.message || `删除${deleteType.value === 'category' ? '分类' : '标签'}失败`)
  } finally {
    saving.value = false
  }
}

async function handleMigrateAndDeleteTag() {
  if (!deletingTag.value || !targetMigrateTagId.value) return
  saving.value = true
  try {
    // 先迁移
    await apiClient.migrateTagMaterials(deletingTag.value.id, targetMigrateTagId.value)
    // 再删除
    await apiClient.deleteMaterialTag(deletingTag.value.id)
    ElMessage.success('标签迁移并删除成功')
    showTagDeleteDialog.value = false
    fetchCategoryTree()
    if (selectedTagId.value === deletingTag.value.id) {
      selectedTagId.value = 'all'
      fetchMaterials()
    }
    deletingTag.value = null
    tagStats.value = null
    targetMigrateTagId.value = null
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    saving.value = false
  }
}

// 批量迁移素材（支持多选标签）
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
    await apiClient.batchUpdateMaterialStatus(selectedIds.value.map(id => Number(id)), 'available')
    ElMessage.success(`已成功启用 ${selectedIds.value.length} 个素材`)
    selectedIds.value = []
    fetchMaterials()
    fetchCategoryTree()
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
    await apiClient.batchUpdateMaterialStatus(selectedIds.value.map(id => Number(id)), 'disabled')
    ElMessage.success(`已成功禁用 ${selectedIds.value.length} 个素材`)
    selectedIds.value = []
    fetchMaterials()
    fetchCategoryTree()
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
  batchCopyTargetAdminId.value = null
  batchCopyTargetPlatformId.value = null
  batchCopyTargetCategoryId.value = null
  batchCopyTargetTagIds.value = []
  showBatchCopyDialog.value = true
}

// 批量删除
async function handleBatchDelete() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的素材')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 个素材吗？此操作不可恢复！`,
      '批量删除',
      { type: 'warning' }
    )
    // 记录删除前的素材信息
    const deletedMaterials = materialList.value
      .filter(m => selectedIds.value.includes(m.id))
      .map(m => ({ id: m.id, title: m.title, topic: m.topic }))
    await apiClient.batchDeleteMaterials(selectedIds.value.map(id => Number(id)))
    ElMessage.success('素材删除成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_MATERIALS,
      action: 'delete',
      description: `批量删除素材：${deletedMaterials.length}个素材`,
      table_name: 'material',
      extra_data: { deleted_materials: deletedMaterials }
    })
    selectedIds.value = []
    fetchMaterials()
    fetchCategoryTree()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '批量删除失败')
    }
  }
}

// 超级管理员切换目标管理员时：清空已选（批量复制用）
function handleBatchCopyAdminChange() {
  // 切换管理员时，重置平台、分类、标签选择
  batchCopyTargetPlatformId.value = null
  batchCopyTargetCategoryId.value = null
  batchCopyTargetTagIds.value = []
}

// 切换平台时：清空已选分类、标签（批量复制用）
function handleBatchCopyPlatformChange() {
  batchCopyTargetCategoryId.value = null
  batchCopyTargetTagIds.value = []
}

// 切换分类时：清空已选标签（批量复制用）
function handleBatchCopyCategoryChange() {
  batchCopyTargetTagIds.value = []
}

// 确认批量复制
async function confirmBatchCopy() {
  if (selectedIds.value.length === 0) return
  if (!batchCopyTargetPlatformId.value || !batchCopyTargetCategoryId.value) return
  if (batchCopyTargetTagIds.value.length === 0) {
    ElMessage.warning('请选择目标标签')
    return
  }

  saving.value = true
  try {
    const params: any = {
      material_ids: selectedIds.value.map(id => Number(id)),
      target_platform_id: batchCopyTargetPlatformId.value,
      target_category_id: batchCopyTargetCategoryId.value,
      target_tag_ids: batchCopyTargetTagIds.value
    }

    // 超级管理员：添加目标管理员参数
    if (isSuperAdmin.value && batchCopyTargetAdminId.value) {
      params.target_operator_id = batchCopyTargetAdminId.value
    }

    const result = await apiClient.batchCopyMaterials(params)
    if (result.failed_ids && result.failed_ids.length > 0) {
      ElMessage.warning(`成功复制 ${result.success_count} 个素材，${result.failed_ids.length} 个素材复制失败`)
    } else {
      ElMessage.success(`已成功复制 ${result.success_count} 个素材`)
    }
    showBatchCopyDialog.value = false
    selectedIds.value = []
    fetchMaterials()
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '批量复制失败')
  } finally {
    saving.value = false
  }
}

// 超级管理员切换目标管理员时：加载该管理员的标签并清空已选
async function handleBatchMigrateAdminChange() {
  // 切换管理员时，重置平台、分类、标签选择
  batchMigrateTargetPlatformId.value = null
  batchMigrateTargetCategoryId.value = null
  batchMigrateTargetTagIds.value = []
  if (batchMigrateTargetAdminId.value) {
    try {
      // 获取该管理员的所有标签
      const treeData = await apiClient.getMaterialPlatformTree({
        owner_operator_id: batchMigrateTargetAdminId.value
      })
      // 从树数据中提取所有标签
      const allTags: MaterialTag[] = []
      treeData.platforms.forEach((platform: any) => {
        platform.categories?.forEach((category: any) => {
          category.tags?.forEach((tag: any) => {
            allTags.push(tag as unknown as MaterialTag)
          })
        })
      })
      batchMigrateAvailableTags.value = allTags
    } catch (error: any) {
      console.error('加载目标管理员标签失败:', error)
      batchMigrateAvailableTags.value = []
    }
  } else {
    batchMigrateAvailableTags.value = []
  }
}

// 切换平台时：清空已选分类、标签（批量迁移用）
function handleBatchMigratePlatformChange() {
  batchMigrateTargetCategoryId.value = null
  batchMigrateTargetTagIds.value = []
}

// 切换分类时：清空已选标签（批量迁移用）
function handleBatchMigrateCategoryChange() {
  batchMigrateTargetTagIds.value = []
}

async function confirmBatchMigrate() {
  if (selectedIds.value.length === 0) return
  if (!batchMigrateTargetPlatformId.value || !batchMigrateTargetCategoryId.value) return
  if (batchMigrateTargetTagIds.value.length === 0) {
    ElMessage.warning('请选择目标标签')
    return
  }

  saving.value = true
  try {
    if (isSuperAdmin.value) {
      // 超级管理员：调用批量迁移API（素材所有权转移）
      const result = await apiClient.batchTransferMaterials({
        material_ids: selectedIds.value.map(id => Number(id)),
        target_operator_id: batchMigrateTargetAdminId.value!,
        target_platform_id: batchMigrateTargetPlatformId.value,
        target_category_id: batchMigrateTargetCategoryId.value,
        target_tag_ids: batchMigrateTargetTagIds.value
      })
      if (result.failed_count > 0) {
        ElMessage.warning(`成功迁移 ${result.success_count} 个素材，${result.failed_count} 个素材迁移失败`)
      } else {
        ElMessage.success(`成功迁移 ${result.success_count} 个素材到目标管理员`)
      }
    } else {
      // 创作管理员：替换素材的标签（增加和删减都支持）
      for (const materialId of selectedIds.value) {
        await apiClient.updateMaterial(materialId, {
          tag_ids: batchMigrateTargetTagIds.value
        })
      }
      ElMessage.success(`已成功更新 ${selectedIds.value.length} 个素材的标签`)
    }
    showBatchMigrateDialog.value = false
    selectedIds.value = []
    fetchMaterials()
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '批量迁移失败')
  } finally {
    saving.value = false
  }
}

function handleEdit(material: Material) {
  console.log('[MaterialList] handleEdit called with material:', material)
  console.log('[MaterialList] material.platform:', material.platform)
  console.log('[MaterialList] material.category:', material.category)
  console.log('[MaterialList] material.tags:', material.tags)

  // 重置删除附件列表
  deletedAttachmentIds.value = []

  editForm.id = material.id
  editForm.title = material.title
  editForm.content = material.content || ''
  editForm.topic = material.topic || ''
  editForm.content_type = material.content_type as 'text' | 'image_text' | 'video'
  editForm.text_content = material.text_content || ''

  // 直接使用后端返回的 platform 和 category 信息
  if (material.platform?.id) {
    editForm.platform_id = material.platform.id
  }
  if (material.category?.id) {
    editForm.category_id = material.category.id
  }

  editForm.tag_ids = material.tags?.map(t => t.id) || []
  editForm.source_url = material.source_url || ''
  // 加载已有图片
  editForm.images = (material.attachments || [])
    .filter(a => a.file_type === 'image')
    .map(a => ({ url: getFullImageUrl(a.file_url), id: a.id }))
  showEditDialog.value = true
}

async function handleSaveEdit() {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    // 收集新上传的文件
    const newFiles = editForm.images
      .filter(img => img.file)
      .map(img => img.file!)

    const newValue = {
      title: editForm.title,
      content: editForm.content,
      topic: editForm.topic,
      content_type: editForm.content_type,
      text_content: editForm.text_content,
      tag_ids: editForm.tag_ids,
      platform_id: editForm.platform_id,
      category_id: editForm.category_id,
      source_url: editForm.source_url
    }

    await apiClient.updateMaterialWithAttachments({
      id: editForm.id,
      title: editForm.title,
      content: editForm.content,
      topic: editForm.topic,
      content_type: editForm.content_type,
      text_content: editForm.text_content || undefined,
      tag_ids: editForm.tag_ids,
      platform_id: editForm.platform_id,
      category_id: editForm.category_id,
      source_url: editForm.source_url || undefined,
      delete_attachment_ids: deletedAttachmentIds.value.length > 0 ? deletedAttachmentIds.value : undefined,
      files: newFiles.length > 0 ? newFiles : undefined
    })
    ElMessage.success('素材已保存')
    // 记录操作日志
    await logOperation({
      module: MODULE_MATERIALS,
      action: 'update',
      description: `更新素材：${editForm.title}`,
      table_name: 'material',
      record_id: editForm.id,
      new_value: newValue
    })
    showEditDialog.value = false
    fetchMaterials()
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '保存素材失败')
  } finally {
    saving.value = false
  }
}

// 打开复制弹窗
async function handleCopy(material: Material) {
  copyingMaterial.value = material
  copyNewTitle.value = `${material.title} - 副本`
  copyTargetAdminId.value = null
  copyTargetPlatformId.value = null
  copyTargetCategoryId.value = null
  copyTargetTagIds.value = []
  copyAvailableTags.value = []
  showCopyDialog.value = true

  // 记录操作日志
  await logOperation({
    module: MODULE_MATERIALS,
    action: 'copy',
    description: `复制素材：${material.title}`,
    table_name: 'material',
    record_id: material.id,
    extra_data: { source_material_title: material.title }
  })

  // 创作管理员默认设置为自己的ID并加载自己的标签
  if (!isSuperAdmin.value) {
    copyTargetAdminId.value = currentUserId.value || null
    // 加载当前创作管理员自己的标签
    try {
      const treeData = await apiClient.getMaterialPlatformTree({
        owner_operator_id: currentUserId.value || undefined
      })
      // 从树数据中提取所有标签
      const allTags: MaterialTag[] = []
      treeData.platforms.forEach(platform => {
        platform.categories?.forEach(category => {
          category.tags?.forEach(tag => {
            allTags.push(tag as unknown as MaterialTag)
          })
        })
      })
      copyAvailableTags.value = allTags
    } catch (error: any) {
      console.error('加载标签失败:', error)
      copyAvailableTags.value = []
    }
    // 默认复制原素材的标签，如果原素材无标签则为空数组
    const originalTags = material.tags?.map(t => t.id) || []
    copyTargetTagIds.value = originalTags
  }
}

// 切换目标管理员时：重置平台、分类、标签
function handleCopyPlatformChange() {
  copyTargetCategoryId.value = null
  copyTargetTagIds.value = []
}

function handleCopyCategoryChange() {
  copyTargetTagIds.value = []
}

// 切换目标管理员时：加载该管理员的标签并清空已选
async function handleCopyAdminChange() {
  copyTargetPlatformId.value = null
  copyTargetCategoryId.value = null
  copyTargetTagIds.value = []
  if (copyTargetAdminId.value) {
    try {
      const treeData = await apiClient.getMaterialPlatformTree({
        owner_operator_id: copyTargetAdminId.value
      })
      const allTags: MaterialTag[] = []
      treeData.platforms.forEach(platform => {
        platform.categories?.forEach(category => {
          category.tags?.forEach(tag => {
            allTags.push(tag as unknown as MaterialTag)
          })
        })
      })
      copyAvailableTags.value = allTags
    } catch (error: any) {
      console.error('加载目标管理员标签失败:', error)
      copyAvailableTags.value = []
    }
  } else {
    copyAvailableTags.value = []
  }
}

// 确认复制
async function confirmCopy() {
  if (!copyingMaterial.value || !copyNewTitle.value.trim() || copyTargetTagIds.value.length === 0) return
  if (isSuperAdmin.value && (!copyTargetAdminId.value || !copyTargetPlatformId.value || !copyTargetCategoryId.value)) return

  saving.value = true
  try {
    const targetAdminId = isSuperAdmin.value ? copyTargetAdminId.value : currentUserId.value

    // 调用新的复制API，支持指定目标管理员和标签
    await apiClient.copyMaterial(copyingMaterial.value.id, {
      title: copyNewTitle.value.trim(),
      target_operator_id: targetAdminId!,
      tag_ids: copyTargetTagIds.value
    })

    ElMessage.success('素材复制成功')
    showCopyDialog.value = false
    copyingMaterial.value = null
    fetchMaterials()
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '复制素材失败')
  } finally {
    saving.value = false
  }
}

// 打开管理素材标签弹窗
function handleManageMaterialTags(material: Material) {
  managingMaterial.value = { ...material }
  newMaterialTagIds.value = []
  removedMaterialTagIds.value = []
  showManageTagsDialog.value = true
}

// 移除素材标签（仅本地记录，点击保存时才提交）
function handleRemoveMaterialTag(tagId: number) {
  if (!managingMaterial.value) return

  // 从本地tags中移除
  managingMaterial.value.tags = (managingMaterial.value.tags || []).filter(t => t.id !== tagId)
  removedMaterialTagIds.value.push(tagId)
}

// 保存素材标签变更
async function saveMaterialTags() {
  if (!managingMaterial.value) return

  saving.value = true
  try {
    // 构建新的标签列表：保留未移除的标签 + 新添加的标签
    const currentTagIds = (managingMaterial.value.tags || []).map(t => t.id)
    const finalTagIds = [...currentTagIds, ...newMaterialTagIds.value]

    // 更新素材标签
    await apiClient.updateMaterial(managingMaterial.value.id, {
      tag_ids: finalTagIds
    })

    ElMessage.success('素材标签已更新')
    showManageTagsDialog.value = false
    managingMaterial.value = null
    newMaterialTagIds.value = []
    removedMaterialTagIds.value = []
    fetchMaterials()
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '更新素材标签失败')
  } finally {
    saving.value = false
  }
}

async function handleToggleStatus(material: Material) {
  try {
    const newStatus = material.status === 'available' ? 'disabled' : 'available'
    await apiClient.updateMaterial(material.id, { status: newStatus })
    ElMessage.success(newStatus === 'available' ? '已启用' : '已禁用')
    // 记录操作日志
    await logOperation({
      module: MODULE_MATERIALS,
      action: newStatus === 'available' ? 'enable' : 'disable',
      description: `${newStatus === 'available' ? '启用' : '禁用'}素材：${material.title}`,
      table_name: 'material',
      record_id: material.id,
      old_value: { status: material.status },
      new_value: { status: newStatus }
    })
    fetchMaterials()
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

async function handleDelete(material: Material) {
  try {
    await ElMessageBox.confirm(
      `确定要删除素材「${material.title}」吗？此操作不可恢复！`,
      '确认删除',
      { type: 'warning' }
    )
    const oldValue = {
      title: material.title,
      content: material.content,
      topic: material.topic
    }
    await apiClient.deleteMaterial(material.id)
    ElMessage.success('素材删除成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_MATERIALS,
      action: 'delete',
      description: `删除素材：${material.title}`,
      table_name: 'material',
      record_id: material.id,
      old_value: oldValue
    })
    fetchMaterials()
    fetchCategoryTree()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除素材失败')
    }
  }
}

async function handleUpload() {
  if (!uploadFormRef.value) return

  try {
    await uploadFormRef.value.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    // 使用新的 uploadMaterial API 一次性上传素材和图片
    const newMaterial = await apiClient.uploadMaterial({
      title: uploadForm.title,
      content: uploadForm.content,
      topic: uploadForm.topic,
      content_type: uploadForm.content_type,
      text_content: uploadForm.text_content || undefined,
      tag_ids: uploadForm.tag_ids,
      source_url: uploadForm.source_url || undefined,
      files: uploadForm.images.map(img => img.file).filter(Boolean) as File[]
    })

    ElMessage.success('素材上传成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_MATERIALS,
      action: 'create',
      description: `上传素材：${uploadForm.title}`,
      table_name: 'material',
      record_id: newMaterial?.id,
      new_value: {
        title: uploadForm.title,
        content: uploadForm.content,
        topic: uploadForm.topic,
        content_type: uploadForm.content_type,
        text_content: uploadForm.text_content,
        tag_ids: uploadForm.tag_ids
      }
    })
    showUploadDialog.value = false
    // 重置表单
    uploadForm.title = ''
    uploadForm.content = ''
    uploadForm.topic = ''
    uploadForm.content_type = 'image_text'
    uploadForm.text_content = ''
    uploadForm.category_id = undefined
    uploadForm.tag_ids = []
    uploadForm.source_url = ''
    uploadForm.images = []
    fetchMaterials()
    fetchCategoryTree()
  } catch (error: any) {
    ElMessage.error(error.message || '上传素材失败')
  } finally {
    saving.value = false
  }
}

// 图片上传前处理
function beforeImageUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  const isLt20M = file.size / 1024 / 1024 < 20

  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  if (!isLt20M) {
    ElMessage.error(`图片大小不能超过 20MB！当前文件大小：${(file.size / 1024 / 1024).toFixed(2)}MB`)
    return false
  }

  // 创建本地预览URL
  const url = URL.createObjectURL(file)
  uploadForm.images.push({ url, file })
  return false // 阻止自动上传，我们手动处理
}

// 移除上传图片
function removeUploadImage(index: number) {
  uploadForm.images.splice(index, 1)
}

// 编辑时图片上传前处理
function beforeEditImageUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  const isLt20M = file.size / 1024 / 1024 < 20

  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  if (!isLt20M) {
    ElMessage.error(`图片大小不能超过 20MB！当前文件大小：${(file.size / 1024 / 1024).toFixed(2)}MB`)
    return false
  }

  const url = URL.createObjectURL(file)
  editForm.images.push({ url, file })
  return false
}

// 移除编辑图片
function removeEditImage(index: number) {
  const image = editForm.images[index]
  if (image.id) {
    // 如果是已有附件，记录到删除列表
    deletedAttachmentIds.value.push(image.id)
  }
  editForm.images.splice(index, 1)
}

function handleSelectionChange(selection: Material[]) {
  selectedIds.value = selection.map(item => item.id)
}
</script>

<style lang="scss" scoped>
@import './materials.scss';

.material-list-view {
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

  &.delete {
    color: #F56C6C;
    &:hover {
      color: #f89898;
    }
  }

  &.add {
    color: #67C23A;
    &:hover {
      color: #95d475;
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

.mb-md {
  margin-bottom: 16px;
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

.material-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.material-card {
  :deep(.el-card__header) {
    padding: 2px 2px;
  }

  :deep(.el-card__body) {
    padding: 2px 2px;
  }

  .card-header {
    .material-title {
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

  .material-preview {
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
  }

  .preview-image {
    width: 100%;
    height: 100%;
  }
}

.image-placeholder,
.image-placeholder-small {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: var(--bg-tertiary);
}

.image-placeholder {
  height: 100px;
}

.image-placeholder-small {
  width: 60px;
  height: 60px;
}

.material-info {
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

.material-actions {
  display: flex;
  justify-content: flex-end;
  flex-wrap: nowrap;
  gap: 2px;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid var(--border-color);

  .el-button--small.is-link {
    padding: 1px 2px;
    font-size: 11px;
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
  gap: 12px;
  flex-wrap: wrap;
}

.image-preview-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 4px;
  overflow: hidden;

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
    border-radius: 50%;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 12px;
    transition: background 0.2s;

    &:hover {
      background: rgba(245, 108, 108, 0.8);
    }
  }
}

.image-uploader {
  width: 100px;
  height: 100px;
}

.upload-placeholder {
  width: 100px;
  height: 100px;
  border: 1px dashed var(--border-color);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-placeholder);
  cursor: pointer;
  transition: border-color 0.2s;

  &:hover {
    border-color: var(--color-primary);
  }

  .el-icon {
    font-size: 24px;
    margin-bottom: 4px;
  }

  span {
    font-size: 12px;
  }
}

.upload-tip {
  color: var(--text-placeholder);
  font-size: 12px;
  margin-top: 8px;
}

.transfer-hint {
  margin-bottom: 16px;
  color: var(--text-secondary);
}

.delete-tag-content {
  p {
    color: var(--text-primary);
    line-height: 1.6;
  }
}

.delete-platform-info {
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 4px;

  p {
    color: var(--text-primary);
    margin: 0 0 8px 0;
  }

  ul {
    margin: 8px 0;
    padding-left: 20px;
    color: var(--text-secondary);

    li {
      margin: 4px 0;
    }
  }

  .error-text {
    color: #f56c6c;
    font-weight: 500;
    margin-top: 12px;
  }

  .success-text {
    color: #67c23a;
    font-weight: 500;
    margin-top: 12px;
  }
}

.batch-migrate-content {
  p {
    color: #303133;
    line-height: 1.6;
  }

  .select-hint {
    margin-top: 6px;
    color: #909399;
    font-size: 12px;
  }
}

.owner-name {
  color: #606266;
  font-size: 13px;
}

.mt-sm {
  margin-top: 8px;
}

.copy-dialog-content,
.manage-tags-content {
  p {
    color: #303133;
    line-height: 1.6;
  }
}

.current-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.no-tags-text {
  color: #909399;
  font-size: 13px;
}

.no-tag-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}

// 图片预览相关样式
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

// 图片预览弹窗样式（适配主题）
.image-preview-content {
  .preview-material-title {
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

// 详情弹窗样式
:deep(.detail-dialog) {
  .el-dialog__body {
    max-height: calc(80vh - 120px);
    overflow-y: auto;
    padding: 16px 20px;
  }

  .material-detail {
    .el-descriptions {
      .el-descriptions__label {
        width: 90px;
        white-space: nowrap;
        flex-shrink: 0;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .el-descriptions__content {
        overflow-wrap: break-word;
        word-break: break-word;
        min-width: 0;
      }
    }
  }
}

.material-detail {
  // 占位，保持类名引用
}

.detail-content {
  max-height: 600px;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;

  &:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
  }
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid var(--color-primary);
}

.detail-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 10px;
  font-size: 14px;

  &:last-child {
    margin-bottom: 0;
  }
}

.detail-label {
  color: #606266;
  width: 90px;
  flex-shrink: 0;
}

.detail-value {
  color: var(--text-primary);
  flex: 1;
}

.detail-text-content {
  background: var(--bg-tertiary);
  padding: 12px;
  border-radius: 4px;
  color: var(--text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
}

.detail-image-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-image-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid #ebeef5;

  &:hover {
    .detail-image-overlay {
      opacity: 1;
    }
  }
}

.detail-image {
  width: 100%;
  height: 100%;
}

.detail-image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: var(--bg-tertiary);
}

.detail-image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.detail-empty {
  color: var(--text-placeholder);
  font-size: 13px;
  font-style: italic;
}

.detail-empty-text {
  color: var(--text-placeholder);
  font-size: 13px;
}

.detail-link {
  color: var(--color-primary);
  text-decoration: none;
  word-break: break-all;
  overflow-wrap: break-word;

  &:hover {
    text-decoration: underline;
  }
}
</style>