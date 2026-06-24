<template>
  <div class="generation-create-view">
    <h2 class="page-title">创建生成任务</h2>

    <div class="card">
      <!-- 模式选择 -->
      <div v-if="currentStep === -1" class="step-panel">
        <h3 class="step-title">请选择创建模式</h3>
        <div class="mode-selection">
          <el-card class="mode-card" shadow="hover" @click="selectMode('custom')">
            <div class="mode-content">
              <el-icon :size="48" color="var(--color-primary)"><Document /></el-icon>
              <h4>自定义文案</h4>
              <p>直接生成内容，不参考对标文案</p>
            </div>
          </el-card>
          <el-card class="mode-card" shadow="hover" @click="selectMode('reference')">
            <div class="mode-content">
              <el-icon :size="48" color="#67C23A"><Collection /></el-icon>
              <h4>对标文案</h4>
              <p>选择参考素材，复刻二创</p>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 步骤流程（选择模式后显示） -->
      <template v-else>
        <el-steps :active="currentStep" class="mb-lg">
          <!-- 对标文案模式步骤 -->
          <template v-if="taskMode === 'reference'">
            <el-step title="模板创作" />
            <el-step title="素材对标" />
            <el-step title="配置模型" />
            <el-step title="选择用户" />
            <el-step title="确认提交" />
          </template>
          <!-- 自定义文案模式步骤 -->
          <template v-else>
            <el-step title="模板创作" />
            <el-step title="配置模型" />
            <el-step title="选择用户" />
            <el-step title="确认提交" />
          </template>
        </el-steps>

        <div class="step-content">
        <!-- ========== 自定义文案：步骤0-模板创作 ========== -->
        <div v-if="taskMode === 'custom' && currentStep === 0" class="step-panel">
          <h3 class="step-title">模板创作</h3>
          <el-row :gutter="20">
            <!-- 超级管理员：左侧显示所有者筛选 -->
            <el-col v-if="isSuperAdmin" :span="4">
              <div class="card category-panel">
                <div class="panel-header flex-between">
                  <span class="panel-title">模板来源</span>
                </div>
                <el-tree
                  :data="templateOwnerTree"
                  :props="treeProps"
                  node-key="id"
                  default-expand-all
                  highlight-current
                  :expand-on-click-node="false"
                  @node-click="handleTemplateOwnerClick"
                >
                  <template #default="{ node, data }">
                    <span class="custom-tree-node">
                      <span class="node-label">
                        {{ node.label }}
                        <span v-if="data.count !== undefined" class="category-count">({{ data.count }})</span>
                      </span>
                    </span>
                  </template>
                </el-tree>
              </div>
            </el-col>

            <!-- 右侧：模板列表 -->
            <el-col :span="isSuperAdmin ? 20 : 24">
              <div class="selector-toolbar">
                <el-input
                  v-model="templateSearch"
                  placeholder="搜索模板名称"
                  :prefix-icon="Search"
                  style="width: 200px;"
                  clearable
                  @keyup.enter="handleTemplateSearch"
                />
                <el-select v-model="selectedTemplatePlatformId" placeholder="平台筛选" clearable style="width: 130px;" @change="handleTemplatePlatformChange">
                  <el-option v-for="platform in templatePlatforms" :key="platform.id" :label="platform.name" :value="platform.id" />
                </el-select>
                <el-select v-model="templateCategoryFilter" placeholder="分类筛选" clearable style="width: 130px;" @change="() => { templatePage = 1; handleTemplateSearch() }">
                  <el-option v-for="category in templateCategories" :key="category.id" :label="category.name" :value="category.id" />
                </el-select>
                <el-select v-model="templateTagFilter" placeholder="标签筛选" clearable style="width: 140px;">
                  <el-option label="全部标签" value="" />
                  <el-option v-for="tag in templateTagsList" :key="tag.id" :label="tag.name" :value="tag.id" />
                </el-select>
                <el-select v-model="templateStatusFilter" placeholder="状态" clearable style="width: 100px;">
                  <el-option label="全部" value="" />
                  <el-option label="启用" value="enabled" />
                  <el-option label="禁用" value="disabled" />
                </el-select>
                <el-select v-model="templateContentTypeFilter" placeholder="内容类型" clearable style="width: 110px;">
                  <el-option label="全部" value="" />
                  <el-option label="纯文本" value="text" />
                  <el-option label="图文" value="image_text" />
                  <el-option label="视频" value="video_text" />
                </el-select>
                <el-button type="primary" :icon="Search" @click="handleTemplateSearch">搜索</el-button>
              </div>

              <el-table
                ref="templateTableRef"
                :data="templates"
                v-loading="loading"
                highlight-current-row
                @row-click="handleTemplateRowClick"
                @selection-change="handleTemplateSelectionChange"
                style="width: 100%; margin-top: 16px;"
                :row-class-name="templateTableRowClassName"
              >
                <el-table-column type="selection" width="50" />
                <el-table-column prop="name" label="模板名称" min-width="200" show-overflow-tooltip />
                <el-table-column prop="description" label="描述" width="200" show-overflow-tooltip />
                <!-- 超级管理员显示所有者 -->
                <el-table-column v-if="isSuperAdmin" label="所属管理员" width="120">
                  <template #default="{ row }">
                    {{ operatorMap[(row as any).owner_admin_id]?.nickname || (row as any).owner_admin_id === authStore.user?.id ? '我' : '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="platform" label="平台" width="100">
                  <template #default="{ row }">
                    {{ row.platform?.name || '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="category" label="分类" width="100">
                  <template #default="{ row }">
                    {{ row.category?.name || '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="content_type" label="内容类型" width="100">
                  <template #default="{ row }">
                    <el-tag size="small" :type="getContentTypeTag(row.content_type)">
                      {{ getContentTypeLabel(row.content_type) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="tags" label="标签" min-width="180">
                  <template #default="{ row }">
                    <el-tag v-for="tag in parseTemplateTags(row.tags)" :key="tag.id" size="small" class="mr-xs">
                      {{ tag.name }}
                    </el-tag>
                    <span v-if="parseTemplateTags(row.tags).length === 0" class="text-muted">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'enabled' ? 'success' : 'info'" size="small">
                      {{ row.status === 'enabled' ? '启用' : '已禁用' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="160">
                  <template #default="{ row }">
                    {{ formatDate(row.created_at) }}
                  </template>
                </el-table-column>
              </el-table>

              <div class="pagination-wrapper">
                <el-pagination
                  v-model:current-page="templatePage"
                  v-model:page-size="templatePageSize"
                  :page-sizes="[10, 20, 50]"
                  :total="templatesTotal"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="handleTemplateSearch"
                  @current-change="handleTemplatePageChange"
                />
              </div>

              <div v-if="selectedTemplate" class="selected-preview">
                <el-alert title="已选择模板" type="success" :closable="false">
                  <template #default>
                    <span><strong>{{ selectedTemplate.name }}</strong> (ID: {{ selectedTemplate.id }})</span>
                    <el-button type="danger" size="small" link @click="clearSelectedTemplate">清除选择</el-button>
                  </template>
                </el-alert>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- ========== 对标文案：步骤0-模板创作 ========== -->
        <div v-if="taskMode === 'reference' && currentStep === 0" class="step-panel">
          <h3 class="step-title">模板创作</h3>
          <el-row :gutter="20">
            <!-- 超级管理员：左侧显示所有者筛选 -->
            <el-col v-if="isSuperAdmin" :span="4">
              <div class="card category-panel">
                <div class="panel-header flex-between">
                  <span class="panel-title">模板来源</span>
                </div>
                <el-tree
                  :data="templateOwnerTree"
                  :props="treeProps"
                  node-key="id"
                  default-expand-all
                  highlight-current
                  :expand-on-click-node="false"
                  @node-click="handleTemplateOwnerClick"
                >
                  <template #default="{ node, data }">
                    <span class="custom-tree-node">
                      <span class="node-label">
                        {{ node.label }}
                        <span v-if="data.count !== undefined" class="category-count">({{ data.count }})</span>
                      </span>
                    </span>
                  </template>
                </el-tree>
              </div>
            </el-col>

            <!-- 右侧：模板列表 -->
            <el-col :span="isSuperAdmin ? 20 : 24">
              <div class="selector-toolbar">
                <el-input
                  v-model="templateSearch"
                  placeholder="搜索模板名称"
                  :prefix-icon="Search"
                  style="width: 200px;"
                  clearable
                  @keyup.enter="handleTemplateSearch"
                />
                <el-select v-model="selectedTemplatePlatformId" placeholder="平台筛选" clearable style="width: 130px;" @change="handleTemplatePlatformChange">
                  <el-option v-for="platform in templatePlatforms" :key="platform.id" :label="platform.name" :value="platform.id" />
                </el-select>
                <el-select v-model="templateCategoryFilter" placeholder="分类筛选" clearable style="width: 130px;" @change="() => { templatePage = 1; handleTemplateSearch() }">
                  <el-option v-for="category in templateCategories" :key="category.id" :label="category.name" :value="category.id" />
                </el-select>
                <el-select v-model="templateTagFilter" placeholder="标签筛选" clearable style="width: 140px;">
                  <el-option label="全部标签" value="" />
                  <el-option v-for="tag in templateTagsList" :key="tag.id" :label="tag.name" :value="tag.id" />
                </el-select>
                <el-select v-model="templateStatusFilter" placeholder="状态" clearable style="width: 100px;">
                  <el-option label="全部" value="" />
                  <el-option label="启用" value="enabled" />
                  <el-option label="禁用" value="disabled" />
                </el-select>
                <el-select v-model="templateContentTypeFilter" placeholder="内容类型" clearable style="width: 110px;">
                  <el-option label="全部" value="" />
                  <el-option label="纯文本" value="text" />
                  <el-option label="图文" value="image_text" />
                  <el-option label="视频" value="video_text" />
                </el-select>
                <el-button type="primary" :icon="Search" @click="handleTemplateSearch">搜索</el-button>
              </div>

              <el-table
                ref="templateTableRef"
                :data="templates"
                v-loading="loading"
                highlight-current-row
                @row-click="handleTemplateRowClick"
                @selection-change="handleTemplateSelectionChange"
                style="width: 100%; margin-top: 16px;"
                :row-class-name="templateTableRowClassName"
              >
                <el-table-column type="selection" width="50" />
                <el-table-column prop="name" label="模板名称" min-width="200" show-overflow-tooltip />
                <el-table-column prop="description" label="描述" width="200" show-overflow-tooltip />
                <!-- 超级管理员显示所有者 -->
                <el-table-column v-if="isSuperAdmin" label="所属管理员" width="120">
                  <template #default="{ row }">
                    {{ operatorMap[(row as any).owner_admin_id]?.nickname || (row as any).owner_admin_id === authStore.user?.id ? '我' : '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="platform" label="平台" width="100">
                  <template #default="{ row }">
                    {{ row.platform?.name || '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="category" label="分类" width="100">
                  <template #default="{ row }">
                    {{ row.category?.name || '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="content_type" label="内容类型" width="100">
                  <template #default="{ row }">
                    <el-tag size="small" :type="getContentTypeTag(row.content_type)">
                      {{ getContentTypeLabel(row.content_type) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="tags" label="标签" min-width="180">
                  <template #default="{ row }">
                    <el-tag v-for="tag in parseTemplateTags(row.tags)" :key="tag.id" size="small" class="mr-xs">
                      {{ tag.name }}
                    </el-tag>
                    <span v-if="parseTemplateTags(row.tags).length === 0" class="text-muted">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'enabled' ? 'success' : 'info'" size="small">
                      {{ row.status === 'enabled' ? '启用' : '已禁用' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="160">
                  <template #default="{ row }">
                    {{ formatDate(row.created_at) }}
                  </template>
                </el-table-column>
              </el-table>

              <div class="pagination-wrapper">
                <el-pagination
                  v-model:current-page="templatePage"
                  v-model:page-size="templatePageSize"
                  :page-sizes="[10, 20, 50]"
                  :total="templatesTotal"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="handleTemplateSearch"
                  @current-change="handleTemplatePageChange"
                />
              </div>

              <div v-if="selectedTemplate" class="selected-preview">
                <el-alert title="已选择模板" type="success" :closable="false">
                  <template #default>
                    <span><strong>{{ selectedTemplate.name }}</strong> (ID: {{ selectedTemplate.id }})</span>
                    <el-button type="danger" size="small" link @click="clearSelectedTemplate">清除选择</el-button>
                  </template>
                </el-alert>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- ========== 对标文案：步骤1-素材对标 ========== -->
        <div v-if="taskMode === 'reference' && currentStep === 1" class="step-panel">
          <h3 class="step-title">素材对标</h3>
          <el-row :gutter="20">
            <!-- 超级管理员：左侧显示所有者筛选 -->
            <el-col v-if="isSuperAdmin" :span="4">
              <div class="card category-panel">
                <div class="panel-header flex-between">
                  <span class="panel-title">素材来源</span>
                </div>
                <el-tree
                  :data="materialOwnerTree"
                  :props="treeProps"
                  node-key="id"
                  default-expand-all
                  highlight-current
                  :expand-on-click-node="false"
                  @node-click="handleBenchmarkMaterialOwnerClick"
                >
                  <template #default="{ node, data }">
                    <span class="custom-tree-node">
                      <span class="node-label">
                        {{ node.label }}
                        <span v-if="data.count !== undefined" class="category-count">({{ data.count }})</span>
                      </span>
                    </span>
                  </template>
                </el-tree>
              </div>
            </el-col>

            <!-- 右侧素材对标库列表 -->
            <el-col :span="isSuperAdmin ? 20 : 24">
              <div class="selector-toolbar">
                <el-input
                  v-model="benchmarkMaterialSearch"
                  placeholder="搜索素材标题"
                  :prefix-icon="Search"
                  style="width: 200px;"
                  clearable
                  @keyup.enter="handleBenchmarkMaterialSearch"
                />
                <el-select v-model="benchmarkMaterialPlatformFilter" placeholder="平台筛选" clearable style="width: 130px;" @change="handleBenchmarkMaterialPlatformChange">
                  <el-option v-for="platform in materialPlatforms" :key="platform.id" :label="platform.name" :value="platform.id" />
                </el-select>
                <el-select v-model="benchmarkMaterialCategoryFilter" placeholder="分类筛选" clearable style="width: 130px;" @change="() => { benchmarkMaterialPage = 1; handleBenchmarkMaterialSearch() }">
                  <el-option v-for="category in materialCategories" :key="category.id" :label="category.name" :value="category.id" />
                </el-select>
                <el-select v-model="benchmarkMaterialTagFilter" placeholder="标签筛选" clearable style="width: 140px;">
                  <el-option label="全部标签" value="" />
                  <el-option v-for="tag in materialTags" :key="tag.id" :label="tag.name" :value="tag.id" />
                </el-select>
                <el-select v-model="benchmarkMaterialStatusFilter" placeholder="状态" clearable style="width: 100px;">
                  <el-option label="全部" value="" />
                  <el-option label="可用" value="available" />
                  <el-option label="已禁用" value="disabled" />
                </el-select>
                <el-select v-model="benchmarkMaterialContentTypeFilter" placeholder="内容类型" clearable style="width: 110px;">
                  <el-option label="全部" value="" />
                  <el-option label="纯文本" value="text" />
                  <el-option label="图文" value="image_text" />
                  <el-option label="视频文字" value="video_text" />
                  <el-option label="混合" value="mix" />
                </el-select>
                <el-button type="primary" :icon="Search" @click="handleBenchmarkMaterialSearch">搜索</el-button>
              </div>

              <el-table
                ref="benchmarkMaterialTableRef"
                :data="benchmarkMaterials"
                v-loading="loading"
                highlight-current-row
                @row-click="handleBenchmarkMaterialRowClick"
                @selection-change="handleBenchmarkMaterialSelectionChange"
                style="width: 100%; margin-top: 16px;"
                :row-class-name="benchmarkTableRowClassName"
              >
                <el-table-column type="selection" width="50" />
                <el-table-column label="预览" width="120">
                  <template #default="{ row }">
                    <el-image
                      v-if="row.attachments && row.attachments.length > 0"
                      :src="row.attachments[0].thumbnail_url || row.attachments[0].file_url || 'https://via.placeholder.com/80x60?text=Material'"
                      fit="cover"
                      style="width: 80px; height: 60px; border-radius: 4px;"
                    />
                    <el-image
                      v-else
                      src="https://via.placeholder.com/80x60?text=Material"
                      fit="cover"
                      style="width: 80px; height: 60px; border-radius: 4px;"
                    />
                  </template>
                </el-table-column>
                <el-table-column prop="title" label="素材标题" min-width="200" show-overflow-tooltip />
                <el-table-column prop="topic" label="话题" width="120" show-overflow-tooltip />
                <!-- 超级管理员显示所有者 -->
                <el-table-column v-if="isSuperAdmin" label="所属管理员" width="120">
                  <template #default="{ row }">
                    {{ operatorMap[(row as any).owner_admin_id]?.nickname || (row as any).owner_admin_id === authStore.user?.id ? '我' : '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="content_type" label="内容类型" width="100">
                  <template #default="{ row }">
                    <el-tag size="small" :type="getContentTypeTag(row.content_type)">
                      {{ getContentTypeLabel(row.content_type) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="tags" label="标签" min-width="180">
                  <template #default="{ row }">
                    <el-tag v-for="tag in parseTags(row.tags)" :key="tag" size="small" class="mr-xs">
                      {{ tag }}
                    </el-tag>
                    <span v-if="parseTags(row.tags).length === 0" class="text-muted">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'available' ? 'success' : 'info'" size="small">
                      {{ row.status === 'available' ? '可用' : '已禁用' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="160">
                  <template #default="{ row }">
                    {{ formatDate(row.created_at) }}
                  </template>
                </el-table-column>
              </el-table>

              <div class="pagination-wrapper">
                <el-pagination
                  v-model:current-page="benchmarkMaterialPage"
                  v-model:page-size="benchmarkMaterialPageSize"
                  :page-sizes="[10, 20, 50]"
                  :total="benchmarkMaterialsTotal"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="handleBenchmarkMaterialSearch"
                  @current-change="handleBenchmarkMaterialPageChange"
                />
              </div>

              <div v-if="selectedMaterial" class="selected-preview">
                <el-alert title="已选择素材" type="success" :closable="false">
                  <template #default>
                    <span><strong>{{ selectedMaterial.title }}</strong> (ID: {{ selectedMaterial.id }})</span>
                    <el-button type="danger" size="small" link @click="clearSelectedMaterial">清除选择</el-button>
                  </template>
                </el-alert>
              </div>

              <!-- 对标配置 -->
              <div v-if="selectedMaterial" class="benchmark-config">
                <el-divider content-position="left">对标配置</el-divider>
                <el-form label-width="120px" style="max-width: 700px;">
                  <el-form-item label="文案对标">
                    <el-switch v-model="benchmarkConfig.text_enabled" />
                    <span style="margin-left: 8px; color: #909399; font-size: 13px;">
                      使用对标素材的标题、正文、话题进行二次创作（去重率>80%）
                    </span>
                  </el-form-item>

                  <el-form-item label="图片对标">
                    <el-switch v-model="benchmarkConfig.image_enabled" />
                    <span style="margin-left: 8px; color: #909399; font-size: 13px;">
                      参考对标素材的图片进行生成
                    </span>
                  </el-form-item>

                  <!-- 图片角色配置（当有对标图片时显示） -->
                  <template v-if="benchmarkConfig.image_enabled && getBenchmarkImages().length > 0">
                    <el-divider content-position="left" style="margin: 16px 0 12px;">
                      <span style="font-size: 13px; color: #606266;">图片角色配置</span>
                    </el-divider>
                    <div class="image-role-config">
                      <div v-for="(img, idx) in getBenchmarkImages()" :key="idx" class="role-item">
                        <div class="role-item-header">
                          <el-image
                            :src="img.thumbnail_url || img.file_url"
                            style="width: 60px; height: 45px; border-radius: 4px;"
                            fit="cover"
                          />
                          <span class="role-item-label">对标图{{ idx + 1 }}</span>
                        </div>
                        <el-checkbox-group
                          v-model="benchmarkConfig.image_roles[`benchmark_${idx + 1}`]"
                          class="role-checkbox-group"
                        >
                          <el-checkbox value="composition">构图参考</el-checkbox>
                          <el-checkbox value="scene">场景参考</el-checkbox>
                          <el-checkbox value="style">风格参考</el-checkbox>
                        </el-checkbox-group>
                      </div>
                    </div>
                    <div style="color: #909399; font-size: 12px; margin-top: 8px;">
                      提示：为每张对标图指定参考维度，生成时将按配置融合多张图片的特征
                    </div>
                  </template>

                  <!-- 产品映射配置（当有模板图片时显示） -->
                  <template v-if="getTemplateImages().length > 0">
                    <el-divider content-position="left" style="margin: 16px 0 12px;">
                      <span style="font-size: 13px; color: #606266;">产品映射配置</span>
                    </el-divider>
                    <div class="product-mapping-config">
                      <div v-for="(img, idx) in getTemplateImages()" :key="idx" class="mapping-item">
                        <div class="mapping-item-header">
                          <el-image
                            :src="img.thumbnail_url || img.file_url"
                            style="width: 60px; height: 45px; border-radius: 4px;"
                            fit="cover"
                          />
                          <span class="mapping-item-label">模板图{{ idx + 1 }}</span>
                        </div>
                        <el-input
                          v-model="benchmarkConfig.product_mapping[`product_${idx + 1}`]"
                          placeholder="如：精华液、面霜"
                          style="flex: 1;"
                          clearable
                        >
                          <template #prepend>包含产品</template>
                        </el-input>
                      </div>
                    </div>
                    <div style="color: #909399; font-size: 12px; margin-top: 8px;">
                      提示：标注模板图中的产品，生成时可将其融合到对标图的场景中
                    </div>
                  </template>
                </el-form>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- ========== 步骤：配置模型 ========== -->
        <div v-if="(taskMode === 'reference' ? currentStep === 2 : currentStep === 1)" class="step-panel">
          <h3 class="step-title">配置模型</h3>
          <el-form label-width="140px" style="max-width: 600px;">
            <el-form-item label="选择模式">
              <el-radio-group v-model="modelConfig.model_selection_mode">
                <el-radio value="auto">自动选择（系统根据内容类型自动选择最佳模型）</el-radio>
                <el-radio value="manual">手动选择（指定使用的模型）</el-radio>
              </el-radio-group>
            </el-form-item>

            <template v-if="modelConfig.model_selection_mode === 'manual'">
              <el-divider content-position="left">手动选择模型</el-divider>
              <el-form-item label="文本模型">
                <el-select v-model="modelConfig.llm_model_id" placeholder="选择文本模型" style="width: 100%;" clearable>
                  <el-option label="使用默认设置" value="" />
                  <el-option v-for="model in llmModels" :key="model.id" :label="getPlatformName(model.platform) + '/' + model.model_name" :value="model.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="图片模型">
                <el-select v-model="modelConfig.image_model_id" placeholder="选择图片模型" style="width: 100%;" clearable>
                  <el-option label="使用默认设置" value="" />
                  <el-option v-for="model in imageModels" :key="model.id" :label="getPlatformName(model.platform) + '/' + model.model_name" :value="model.id" />
                </el-select>
              </el-form-item>
            </template>

            <el-divider class="my-lg" />
            <el-form-item label="生成图片数">
              <el-slider
                v-model="modelConfig.image_count"
                :min="1"
                :max="10"
                :step="1"
                show-input
                style="width: 400px;"
              />
            </el-form-item>
            <el-form-item label="最大并发数">
              <el-slider
                v-model="modelConfig.max_concurrency"
                :min="1"
                :max="100"
                :step="1"
                show-input
                style="width: 400px;"
              />
            </el-form-item>

            <el-divider class="my-lg" />
            <el-form-item label="文案去重检测范围">
              <el-checkbox-group v-model="modelConfig.dedup_scope">
                <el-checkbox label="subuser_history">本创作者所有文案</el-checkbox>
                <el-checkbox label="current_task">本任务所有子任务文案</el-checkbox>
                <el-checkbox label="all_history">所有历史文案</el-checkbox>
              </el-checkbox-group>
              <div class="form-tip">可多选，生成内容将与选中范围的已生成内容进行相似度检测</div>
            </el-form-item>

            <el-divider class="my-lg" />
            <el-form-item label="图片去重检测范围">
              <el-checkbox-group v-model="modelConfig.image_dedup_scope">
                <el-checkbox label="subuser_image_history">本创作者历史图片</el-checkbox>
                <el-checkbox label="current_task_images">本任务所有图片</el-checkbox>
                <el-checkbox label="all_image_history">所有历史图片</el-checkbox>
              </el-checkbox-group>
              <div class="form-tip">可多选，生成图片将与选中范围的历史图片进行视觉相似度检测</div>
            </el-form-item>

            <el-form-item>
              <div class="estimate-info">
                <el-icon><InfoFilled /></el-icon>
                <span class="estimate-text">
                  按 {{ modelConfig.max_concurrency }} 并发计算，{{ selectedUsers.length || 'N' }} 个创作者预计
                  <strong>{{ estimatedDuration }}</strong> 完成
                </span>
              </div>
            </el-form-item>
          </el-form>
        </div>

        <!-- ========== 步骤：选择用户 ========== -->
        <div v-if="(taskMode === 'reference' ? currentStep === 3 : currentStep === 2)" class="step-panel">
          <h3 class="step-title">勾选目标创作者</h3>

          <el-row :gutter="20">
            <!-- 超级管理员：左侧显示创作管理员筛选 -->
            <el-col v-if="isSuperAdmin" :span="4">
              <div class="card category-panel">
                <div class="panel-header flex-between">
                  <span class="panel-title">创作管理员</span>
                </div>
                <div class="category-list">
                  <div
                    class="category-item"
                    :class="{ active: selectedOperatorId === null }"
                    @click="handleOperatorClick(null)"
                  >
                    <span class="category-name">
                      全部用户
                      <span class="category-count">({{ globalAllUsersTotal }})</span>
                    </span>
                  </div>
                  <div
                    v-for="operator in operatorList"
                    :key="operator.id"
                    class="category-item"
                    :class="{ active: selectedOperatorId === operator.id }"
                    @click="handleOperatorClick(operator)"
                  >
                    <span class="category-name">
                      {{ operator.nickname }}
                      <span class="category-count">({{ operatorUserCounts[operator.id] || 0 }})</span>
                    </span>
                  </div>
                </div>
              </div>
            </el-col>

            <!-- 右侧用户列表（超级管理员：16列，创作管理员：24列） -->
            <el-col :span="isSuperAdmin ? 20 : 24">
              <div class="selector-toolbar">
                <el-input
                  v-model="userSearch"
                  placeholder="搜索备注名"
                  :prefix-icon="Search"
                  style="width: 240px;"
                  clearable
                  @keyup.enter="handleUserSearch"
                />
                <el-select v-model="userTagFilter" placeholder="标签筛选" style="width: 160px;" clearable>
                  <el-option v-for="tag in userTagsList" :key="tag.id" :label="tag.name" :value="tag.id" />
                </el-select>
                <el-button type="primary" @click="handleUserSearch">搜索</el-button>
                <el-button @click="handleSelectAllUsers">全选</el-button>
                <el-button @click="handleCancelSelectUsers">取消全选</el-button>
              </div>

              <el-table
                ref="userTableRef"
                :data="users"
                v-loading="loading"
                @selection-change="handleUserSelectionChange"
                style="width: 100%; margin-top: 16px;"
              >
                <el-table-column type="selection" width="50" />
                <el-table-column prop="id" label="ID" width="80" />
                <el-table-column prop="nickname" label="备注名" width="140" />
                <el-table-column prop="display_name" label="自定义昵称" width="140">
                  <template #default="{ row }">
                    {{ row.display_name || '-' }}
                  </template>
                </el-table-column>
                <!-- 超级管理员显示所属创作管理员 -->
                <el-table-column v-if="isSuperAdmin" label="所属创作管理员" width="140">
                  <template #default="{ row }">
                    {{ operatorMap[(row as any).owner_operator_id]?.nickname || '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="user_positioning" label="定位" width="140" show-overflow-tooltip />
                <el-table-column prop="tags" label="标签" min-width="200">
                  <template #default="{ row }">
                    <el-tag v-for="tag in parseUserTags(row.tags)" :key="tag.id" size="small" class="mr-xs" :style="getTagStyle(tag.color)">
                      {{ tag.name }}
                    </el-tag>
                    <span v-if="!parseUserTags(row.tags)?.length" class="text-muted">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'online' ? 'success' : 'info'" size="small">
                      {{ row.status === 'online' ? '在线' : row.status === 'offline' ? '离线' : '禁用' }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>

              <div class="pagination-wrapper">
                <el-pagination
                  v-model:current-page="userPage"
                  v-model:page-size="userPageSize"
                  :page-sizes="[10, 20, 50, 100]"
                  :total="usersTotal"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="handleUserSearch"
                  @current-change="handleUserPageChange"
                />
              </div>

              <div class="selected-summary mt-md">
                已选择 <strong>{{ selectedUsers.length }}</strong> 个创作者（共 {{ usersTotal }} 个）
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- ========== 步骤：确认提交 ========== -->
        <div v-if="(taskMode === 'reference' ? currentStep === 4 : currentStep === 3)" class="step-panel">
          <h3 class="step-title">确认提交</h3>
          <div class="confirmation-summary">
            <el-row :gutter="20">
              <el-col :span="14">
                <div class="mb-md">
                  <label class="task-name-label">任务名称</label>
                  <el-input
                    v-model="taskName"
                    placeholder="请输入任务名称（可选，便于识别）"
                    clearable
                    maxlength="200"
                    show-word-limit
                  />
                </div>
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="创建模式">
                    {{ taskMode === 'reference' ? '对标文案' : '自定义文案' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="模板创作">
                    <template v-if="selectedTemplate">
                      {{ selectedTemplate.name }} (ID: {{ selectedTemplate.id }})
                    </template>
                    <span v-else class="text-muted">未选择</span>
                  </el-descriptions-item>
                  <el-descriptions-item v-if="taskMode === 'reference'" label="素材对标">
                    <template v-if="selectedMaterial">
                      {{ selectedMaterial.title }} (ID: {{ selectedMaterial.id }})
                    </template>
                    <span v-else class="text-muted">未选择</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="模型配置">
                    模式: {{ modelConfig.model_selection_mode === 'auto' ? '自动选择' : '手动选择' }}
                    <template v-if="modelConfig.model_selection_mode === 'manual'">
                      <span v-if="modelConfig.llm_model_id"> | 文本: {{ getSelectedModelName(modelConfig.llm_model_id) }}</span>
                      <span v-if="modelConfig.image_model_id"> | 图片: {{ getSelectedModelName(modelConfig.image_model_id) }}</span>
                      <span v-if="modelConfig.video_model_id"> | 视频: {{ getSelectedModelName(modelConfig.video_model_id) }}</span>
                    </template>
                  </el-descriptions-item>
                  <el-descriptions-item label="并发设置">
                    {{ modelConfig.max_concurrency }} 个同时运行
                  </el-descriptions-item>
                  <el-descriptions-item label="生成图片数">
                    {{ modelConfig.image_count }} 张
                  </el-descriptions-item>
                  <el-descriptions-item label="目标创作者">
                    {{ selectedUsers.length }} 个
                  </el-descriptions-item>
                </el-descriptions>
              </el-col>
              <el-col :span="10">
                <el-card class="estimate-card">
                  <template #header>
                    <div class="card-header flex-between">
                      <span>预估信息</span>
                      <el-tag type="info">实时计算</el-tag>
                    </div>
                  </template>
                  <div class="estimate-item">
                    <span class="label">总任务数</span>
                    <span class="value">{{ selectedUsers.length }} 个</span>
                  </div>
                  <el-divider />
                  <div class="estimate-item">
                    <span class="label">最大并发</span>
                    <span class="value">{{ modelConfig.max_concurrency }} 个</span>
                  </div>
                  <el-divider />
                  <div class="estimate-item">
                    <span class="label">单任务预估</span>
                    <span class="value">1-3 分钟</span>
                  </div>
                  <el-divider />
                  <div class="estimate-item">
                    <span class="label">总预估时长</span>
                    <span class="value highlight">{{ estimatedDuration }}</span>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            <el-alert
              title="提交后系统将开始后台生成任务，您可以在任务列表查看进度"
              type="info"
              show-icon
              class="mt-md"
            />
          </div>
        </div>
      </div>

      <div class="step-actions flex-between mt-lg">
        <el-button @click="prevStep">上一步</el-button>
        <div>
          <el-button v-if="!isLastStep" type="primary" :disabled="!canNextStep" @click="nextStep">下一步</el-button>
          <el-button v-else type="success" :disabled="!canSubmit" @click="submitTask" :loading="submitting">
            提交任务
          </el-button>
        </div>
      </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Document, Collection, InfoFilled } from '@element-plus/icons-vue'
import { apiClient, type OperationLogCreateParams } from '@/api/types'
import type { Material, Template, User, MaterialTag, UserTag as ApiUserTag, TemplateTag, TemplatePlatform } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

// 操作日志模块常量
const MODULE_GENERATION = 'generation'

// 记录操作日志
async function logOperation(params: OperationLogCreateParams) {
  try {
    await apiClient.createOperationLog(params)
  } catch (e) {
    console.error('Failed to log operation:', e)
  }
}

const router = useRouter()
const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.userRole === 'super_admin')

// 模式: -1=选择模式, 'custom'=自定义文案, 'reference'=对标文案
const taskMode = ref<'custom' | 'reference' | null>(null)
const currentStep = ref(-1)
const submitting = ref(false)
const loading = ref(false)
const taskName = ref('')

// ========== 搜索和分页 ==========
// 模板创作库搜索和分页
const materialSearch = ref('')
const materialTagFilter = ref('')
const materialStatusFilter = ref('')
const materialContentTypeFilter = ref('')
const materialPlatformFilter = ref<number | null>(null)
const materialCategoryFilter = ref<number | null>(null)
const materialPage = ref(1)
const materialPageSize = ref(10)
const materialsTotal = ref(0)

// 素材对标库搜索和分页
const benchmarkMaterialSearch = ref('')
const benchmarkMaterialTagFilter = ref('')
const benchmarkMaterialStatusFilter = ref('')
const benchmarkMaterialContentTypeFilter = ref('')
const benchmarkMaterialPlatformFilter = ref<number | null>(null)
const benchmarkMaterialCategoryFilter = ref<number | null>(null)
const benchmarkMaterialPage = ref(1)
const benchmarkMaterialPageSize = ref(10)
const benchmarkMaterialsTotal = ref(0)

const templateSearch = ref('')
const templateTagFilter = ref('')
const templatePage = ref(1)
const templatePageSize = ref(10)
const templatesTotal = ref(0)

const userSearch = ref('')
const userTagFilter = ref('')
const userPage = ref(1)
const userPageSize = ref(20)
const usersTotal = ref(0)

// ========== 数据列表 ==========
const materials = ref<Material[]>([])  // 模板创作库列表
const benchmarkMaterials = ref<Material[]>([])  // 素材对标库列表
const templates = ref<Template[]>([])
const users = ref<User[]>([])
const modelConfigs = ref<any[]>([])

// 素材平台和分类列表
const materialPlatforms = ref<any[]>([])
const materialCategories = ref<any[]>([])

// ========== 标签列表（从后端获取） ==========
const materialTags = ref<MaterialTag[]>([])
const templateTags = ref<string[]>([])
const templateTagsList = ref<TemplateTag[]>([])
const templatePlatforms = ref<TemplatePlatform[]>([])
const userTags = ref<string[]>([])  // 保持向后兼容
const userTagsList = ref<ApiUserTag[]>([])  // 新的完整标签列表

// ========== 模板选择相关 ==========
const selectedTemplatePlatformId = ref<number | null>(null)
const templateStatusFilter = ref('')
const templateContentTypeFilter = ref('')
const templateCategoryFilter = ref<number | null>(null)
const templateCategories = ref<any[]>([])

// 树属性配置
const treeProps = {
  children: 'children',
  label: 'name'
}

// 模板平台树
const templatePlatformTree = computed(() => {
  const children = templatePlatforms.value.map(p => ({
    id: p.id,
    name: p.name,
    count: p.template_count || 0
  }))
  return [
    {
      id: 0,
      name: '全部模板',
      children
    }
  ]
})

// ========== 创作管理员相关（超级管理员用） ==========
const operatorList = ref<User[]>([])
const operatorMap = ref<Record<number, User>>({})
const selectedOperatorId = ref<number | null>(null)
const operatorUserCounts = ref<Record<number, number>>({})
const allUsersTotal = ref(0) // 全部用户数量（不受筛选影响）
const globalAllUsersTotal = ref(0) // 全局全部用户数量（超级管理员用，不受创作管理员筛选影响）

// ========== 素材/模板所有者筛选（超级管理员用） ==========
const materialOwnerFilter = ref<'all' | number>('all')
const templateOwnerFilter = ref<'all' | number>('all')
const operatorMaterialCounts = ref<Record<number, number>>({})
const operatorTemplateCounts = ref<Record<number, number>>({})

// 素材所有者树
const materialOwnerTree = computed(() => {
  if (!isSuperAdmin.value) return []

  const currentUserId = authStore.user?.id

  // 我的素材节点
  const selfNode = {
    id: 'self',
    name: '我的素材',
    count: operatorMaterialCounts.value[currentUserId] || 0
  }

  // 其他创作管理员节点
  const otherOperators = operatorList.value.filter(op => op.id !== currentUserId)
  const othersNode = {
    id: 'others',
    name: '其他创作管理员',
    children: otherOperators.map(op => ({
      id: op.id,
      name: op.nickname || op.userid,
      count: operatorMaterialCounts.value[op.id] || 0
    }))
  }

  return [selfNode, othersNode]
})

// 模板所有者树
const templateOwnerTree = computed(() => {
  if (!isSuperAdmin.value) return []

  const currentUserId = authStore.user?.id

  // 我的模板节点
  const selfNode = {
    id: 'self',
    name: '我的模板',
    count: operatorTemplateCounts.value[currentUserId] || 0
  }

  // 其他创作管理员节点
  const otherOperators = operatorList.value.filter(op => op.id !== currentUserId)
  const othersNode = {
    id: 'others',
    name: '其他创作管理员',
    children: otherOperators.map(op => ({
      id: op.id,
      name: op.nickname || op.userid,
      count: operatorTemplateCounts.value[op.id] || 0
    }))
  }

  return [selfNode, othersNode]
})

// ========== 选中数据 ==========
const selectedMaterial = ref<Material | null>(null)  // 素材对标库选中的素材
const selectedCreationMaterial = ref<Material | null>(null)  // 模板创作库选中的素材
const selectedTemplate = ref<Template | null>(null)
const selectedUsers = ref<User[]>([])

// ========== 图片参考选项 ==========
const imageReferenceOptions = [
  { value: 'composition', label: '构图' },
  { value: 'scene', label: '场景' },
  { value: 'style', label: '风格' }
]

// ========== 对标配置 ==========
const benchmarkConfig = reactive({
  text_enabled: true,  // 文案对标开关
  image_enabled: true,  // 图片对标开关
  image_reference_options: ['composition', 'scene', 'style'] as string[],  // 图片参考选项
  // V3.0: 图片角色配置
  image_roles: {} as Record<string, string[]>,  // 如 {'benchmark_1': ['composition', 'scene']}
  product_mapping: {} as Record<string, string>  // 如 {'product_1': '精华液'}
})

// V3.0: 获取对标素材图片列表
function getBenchmarkImages(): { file_url: string; thumbnail_url?: string }[] {
  if (!selectedMaterial.value?.attachments) return []
  return selectedMaterial.value.attachments
    .filter((att: any) => att.file_type === 'image')
    .map((att: any) => ({
      file_url: att.file_url,
      thumbnail_url: att.thumbnail_url
    }))
}

// V3.0: 获取模板图片列表
function getTemplateImages(): { file_url: string; thumbnail_url?: string }[] {
  if (!selectedTemplate.value?.attachments) return []
  return selectedTemplate.value.attachments
    .filter((att: any) => att.file_type === 'image')
    .map((att: any) => ({
      file_url: att.file_url,
      thumbnail_url: att.thumbnail_url
    }))
}

// ========== Table refs ==========
const materialTableRef = ref()
const benchmarkMaterialTableRef = ref()
const templateTableRef = ref()
const userTableRef = ref()

// ========== 模型配置 ==========
const modelConfig = reactive({
  model_selection_mode: 'auto' as 'auto' | 'manual',
  llm_model_id: '',
  image_model_id: '',
  video_model_id: '',
  max_concurrency: 5,
  image_count: 4,
  dedup_scope: [] as string[],  // 文案去重范围，默认不勾选（勾选后激活去重）
  image_dedup_scope: [] as string[],  // 图片去重范围，默认不勾选（勾选后激活去重）
})

// ========== 步骤计算 ==========
// 是否最后一步（确认页）
const isLastStep = computed(() => {
  if (taskMode.value === 'reference') {
    return currentStep.value === 4  // 对标文案模式：步骤4是确认页
  } else if (taskMode.value === 'custom') {
    return currentStep.value === 3  // 自定义文案模式：步骤3是确认页
  }
  return false
})

// 控制非最后一步的"下一步"按钮是否可用
const canNextStep = computed(() => {
  if (taskMode.value === 'reference') {
    if (currentStep.value === 0) return !!selectedTemplate.value  // 模板创作
    if (currentStep.value === 1) return !!selectedMaterial.value  // 素材对标
    if (currentStep.value === 2) return true  // 模型配置步骤始终可下一步
    if (currentStep.value === 3) return selectedUsers.value.length > 0  // 选择用户
  } else if (taskMode.value === 'custom') {
    if (currentStep.value === 0) return !!selectedTemplate.value  // 模板创作
    if (currentStep.value === 1) return true  // 模型配置步骤始终可下一步
    if (currentStep.value === 2) return selectedUsers.value.length > 0  // 选择用户
  }
  return false
})

// 控制最后一步"提交任务"按钮是否可用
const canSubmit = computed(() => {
  if (taskMode.value === 'reference') {
    return !!selectedTemplate.value && !!selectedMaterial.value && selectedUsers.value.length > 0
  } else if (taskMode.value === 'custom') {
    return !!selectedTemplate.value && selectedUsers.value.length > 0
  }
  return false
})

// ========== 平台列表（从后端 API 动态生成，无需硬编码） ==========

// 平台模型类型配置（从后端 API 动态加载）
const platformModelTypes = ref<Record<string, string[]>>({})

// 动态生成平台列表（从 API 响应 platformModelTypes 提取，直接用 ID 作为显示名）
const platforms = computed(() => {
  const types = platformModelTypes.value || {}
  return Object.keys(types).map(id => ({
    id,
    name: id  // 直接用平台 ID 作为显示名
  }))
})

// 获取平台显示名称（直接用 ID）
const getPlatformName = (platformId: string): string => {
  return platformId
}

// 加载平台模型类型配置
const loadPlatformModelTypes = async () => {
  try {
    const types = await apiClient.getPlatformModelTypes()
    platformModelTypes.value = (types?.platform_types || {}) as Record<string, string[]>
  } catch (error) {
    console.error('加载平台模型类型失败:', error)
  }
}

// ========== 模型列表计算属性 ==========
const llmModels = computed(() => modelConfigs.value.filter((m: any) => m.model_type === 'llm' && m.status === 'active'))
const imageModels = computed(() => modelConfigs.value.filter((m: any) => m.model_type === 'image' && m.status === 'active'))
const videoModels = computed(() => modelConfigs.value.filter((m: any) => m.model_type === 'video' && m.status === 'active'))

const getSelectedModelName = (modelId: number | string): string => {
  const model = modelConfigs.value.find((m: any) => m.id === modelId)
  if (!model) return ''
  return `${getPlatformName(model.platform)}/${model.model_name}`
}

// ========== 预估完成时间 ==========
const estimatedDuration = computed(() => {
  const userCount = selectedUsers.value.length || 1
  const concurrency = modelConfig.max_concurrency
  const avgTimePerTask = 2
  const batches = Math.ceil(userCount / concurrency)
  const totalMinutes = batches * avgTimePerTask

  if (totalMinutes < 60) {
    return `约 ${totalMinutes} 分钟`
  }
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return minutes > 0 ? `约 ${hours} 小时 ${minutes} 分钟` : `约 ${hours} 小时`
})

// ========== 选择模式 ==========
const selectMode = (mode: 'custom' | 'reference') => {
  taskMode.value = mode
  currentStep.value = 0
  // 进入模板创作选择步骤时加载模板列表和分类列表
  handleTemplateSearch()
  fetchTemplateCategories()
}

// ========== 素材相关 ==========
const handleMaterialSearch = async () => {
  loading.value = true
  try {
    const params: any = {
      page: materialPage.value,
      limit: materialPageSize.value,
      keyword: materialSearch.value || undefined,
      tag_id: materialTagFilter.value || undefined,
      library_type: 'creation',  // 模板创作库
      status: materialStatusFilter.value || undefined,
      content_type: materialContentTypeFilter.value || undefined,
      platform_id: materialPlatformFilter.value || undefined,
      category_id: materialCategoryFilter.value || undefined
    }

    // 超级管理员：根据所有者筛选
    if (isSuperAdmin.value) {
      if (materialOwnerFilter.value === 'self') {
        params.owner_operator_id = authStore.user?.id
      } else if (typeof materialOwnerFilter.value === 'number') {
        params.owner_operator_id = materialOwnerFilter.value
      }
      // 'all' = 不传 owner_operator_id = 查询所有
    } else {
      // 创作管理员：只能查看自己的素材
      params.owner_operator_id = authStore.user?.id
    }

    const response = await apiClient.getMaterials(params)
    materials.value = response.items || []
    materialsTotal.value = response.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '获取素材列表失败')
  } finally {
    loading.value = false
  }
}

const handleMaterialPageChange = () => {
  handleMaterialSearch()
}

const handleMaterialRowClick = (row: Material) => {
  const isSelected = selectedMaterial.value?.id === row.id
  // 清除之前的选择
  materialTableRef.value?.clearSelection()
  if (isSelected) {
    // 取消选择
    selectedMaterial.value = null
    selectedCreationMaterial.value = null
  } else {
    // 根据当前模式决定选择哪个变量
    if (taskMode.value === 'reference' && currentStep.value === 0) {
      // 对标模式的步骤0：选择模板创作
      selectedCreationMaterial.value = row
    } else {
      // 自定义模式或其他情况：选择模板创作
      selectedMaterial.value = row
    }
    materialTableRef.value?.toggleRowSelection(row, true)
  }
}

const handleMaterialSelectionChange = (selection: Material[]) => {
  if (selection.length > 1) {
    materialTableRef.value?.clearSelection()
    materialTableRef.value?.toggleRowSelection(selection[selection.length - 1])
  } else if (selection.length === 1) {
    selectedMaterial.value = selection[0]
  } else {
    selectedMaterial.value = null
  }
}

const tableRowClassName = ({ row }: { row: Material }) => {
  return selectedMaterial.value?.id === row.id ? 'selected-row' : ''
}

const clearSelectedMaterial = () => {
  selectedMaterial.value = null
  materialTableRef.value?.clearSelection()
}

const clearSelectedCreationMaterial = () => {
  selectedCreationMaterial.value = null
  materialTableRef.value?.clearSelection()
}



// ========== 素材对标库相关 ==========
const benchmarkMaterialOwnerFilter = ref<'all' | number>('all')

const handleBenchmarkMaterialSearch = async () => {
  loading.value = true
  try {
    const params: any = {
      page: benchmarkMaterialPage.value,
      limit: benchmarkMaterialPageSize.value,
      keyword: benchmarkMaterialSearch.value || undefined,
      tag_id: benchmarkMaterialTagFilter.value || undefined,
      library_type: 'benchmark',  // 素材对标库
      status: benchmarkMaterialStatusFilter.value || undefined,
      content_type: benchmarkMaterialContentTypeFilter.value || undefined,
      platform_id: benchmarkMaterialPlatformFilter.value || undefined,
      category_id: benchmarkMaterialCategoryFilter.value || undefined
    }

    // 超级管理员：根据所有者筛选
    if (isSuperAdmin.value) {
      if (benchmarkMaterialOwnerFilter.value === 'self') {
        params.owner_operator_id = authStore.user?.id
      } else if (typeof benchmarkMaterialOwnerFilter.value === 'number') {
        params.owner_operator_id = benchmarkMaterialOwnerFilter.value
      }
      // 'all' = 不传 owner_operator_id = 查询所有
    } else {
      // 创作管理员：只能查看自己的素材
      params.owner_operator_id = authStore.user?.id
    }

    const response = await apiClient.getMaterials(params)
    benchmarkMaterials.value = response.items || []
    benchmarkMaterialsTotal.value = response.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '获取素材列表失败')
  } finally {
    loading.value = false
  }
}

const handleBenchmarkMaterialPageChange = () => {
  handleBenchmarkMaterialSearch()
}

const handleBenchmarkMaterialRowClick = (row: Material) => {
  const isSelected = selectedMaterial.value?.id === row.id
  // 清除之前的选择
  benchmarkMaterialTableRef.value?.clearSelection()
  if (isSelected) {
    // 取消选择
    selectedMaterial.value = null
  } else {
    // 勾选当前行
    selectedMaterial.value = row
    benchmarkMaterialTableRef.value?.toggleRowSelection(row, true)
  }
}

const handleBenchmarkMaterialSelectionChange = (selection: Material[]) => {
  if (selection.length > 1) {
    benchmarkMaterialTableRef.value?.clearSelection()
    benchmarkMaterialTableRef.value?.toggleRowSelection(selection[selection.length - 1])
  } else if (selection.length === 1) {
    selectedMaterial.value = selection[0]
  } else {
    selectedMaterial.value = null
  }
}

const benchmarkTableRowClassName = ({ row }: { row: Material }) => {
  return selectedMaterial.value?.id === row.id ? 'selected-row' : ''
}

const handleBenchmarkMaterialOwnerClick = (data: any) => {
  if (data.id === 'self') {
    benchmarkMaterialOwnerFilter.value = 'self'
  } else if (typeof data.id === 'number') {
    benchmarkMaterialOwnerFilter.value = data.id
  } else if (data.id === 'others') {
    // 点击"其他创作管理员"父节点，不做筛选
    benchmarkMaterialOwnerFilter.value = 'all'
  } else {
    benchmarkMaterialOwnerFilter.value = 'all'
  }
  benchmarkMaterialPage.value = 1
  handleBenchmarkMaterialSearch()
}

// ========== 标签获取 ==========
const fetchMaterialTags = async () => {
  try {
    const tags = await apiClient.getMaterialTags()
    materialTags.value = tags || []
  } catch (error: any) {
    console.error('获取素材标签失败:', error)
  }
}

// 获取素材平台列表
const fetchMaterialPlatforms = async () => {
  try {
    // 超级管理员获取所有平台，创作管理员获取自己的平台
    const params: any = isSuperAdmin.value ? {} : undefined
    const platforms = await apiClient.getMaterialPlatforms(params)
    materialPlatforms.value = platforms || []
  } catch (error: any) {
    console.error('获取素材平台失败:', error)
  }
}

// 获取素材分类列表（根据平台筛选）
const fetchMaterialCategories = async (platformId?: number) => {
  try {
    const categories = await apiClient.getMaterialCategories(platformId)
    materialCategories.value = categories || []
  } catch (error: any) {
    console.error('获取素材分类失败:', error)
  }
}

// 平台选择变更时加载分类
const handleMaterialPlatformChange = (platformId: number | null) => {
  materialCategoryFilter.value = null
  fetchMaterialCategories(platformId || undefined)  // 清空时加载所有分类
  materialPage.value = 1
  handleMaterialSearch()
}

// 对标素材平台选择变更
const handleBenchmarkMaterialPlatformChange = (platformId: number | null) => {
  benchmarkMaterialCategoryFilter.value = null
  fetchMaterialCategories(platformId || undefined)  // 清空时加载所有分类
  benchmarkMaterialPage.value = 1
  handleBenchmarkMaterialSearch()
}

// ========== 模板相关 ==========
const handleTemplateSearch = async () => {
  loading.value = true
  try {
    const params: any = {
      page: templatePage.value,
      limit: templatePageSize.value,
      keyword: templateSearch.value || undefined
    }
    if (templateStatusFilter.value) params.status = templateStatusFilter.value
    if (templateContentTypeFilter.value) params.content_type = templateContentTypeFilter.value
    if (selectedTemplatePlatformId.value) params.platform_id = selectedTemplatePlatformId.value
    if (templateCategoryFilter.value) params.category_id = templateCategoryFilter.value
    if (templateTagFilter.value) params.tag_id = Number(templateTagFilter.value)

    // 超级管理员：根据所有者筛选
    if (isSuperAdmin.value) {
      if (templateOwnerFilter.value === 'self') {
        params.owner_operator_id = authStore.user?.id
      } else if (typeof templateOwnerFilter.value === 'number') {
        params.owner_operator_id = templateOwnerFilter.value
      }
      // 'all' = 不传 owner_operator_id = 查询所有
    }

    const response = await apiClient.getTemplates(params)
    templates.value = response.items || []
    templatesTotal.value = response.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '获取模板列表失败')
  } finally {
    loading.value = false
  }
}

// 获取模板分类列表（根据平台筛选）
const fetchTemplateCategories = async (platformId?: number) => {
  try {
    const categories = await apiClient.getTemplateCategories(platformId)
    templateCategories.value = categories || []
  } catch (error: any) {
    console.error('获取模板分类失败:', error)
  }
}

// 模板平台选择变更时加载分类
const handleTemplatePlatformChange = (platformId: number | null) => {
  templateCategoryFilter.value = null
  fetchTemplateCategories(platformId || undefined)
  templatePage.value = 1
  handleTemplateSearch()
}

// 模板平台点击处理
const handleTemplatePlatformClick = (data: any) => {
  if (data.id === 0) {
    selectedTemplatePlatformId.value = null
  } else {
    selectedTemplatePlatformId.value = data.id
  }
  templatePage.value = 1
  handleTemplateSearch()
}

// 素材所有者点击处理（超级管理员用）
const handleMaterialOwnerClick = (data: any) => {
  if (data.id === 'self') {
    materialOwnerFilter.value = 'self'
  } else if (typeof data.id === 'number') {
    materialOwnerFilter.value = data.id
  } else if (data.id === 'others') {
    // 点击"其他创作管理员"父节点，不做筛选
    materialOwnerFilter.value = 'all'
  } else {
    materialOwnerFilter.value = 'all'
  }
  materialPage.value = 1
  handleMaterialSearch()
}

// 模板所有者点击处理（超级管理员用）
const handleTemplateOwnerClick = (data: any) => {
  if (data.id === 'self') {
    templateOwnerFilter.value = 'self'
  } else if (typeof data.id === 'number') {
    templateOwnerFilter.value = data.id
  } else if (data.id === 'others') {
    // 点击"其他创作管理员"父节点，不做筛选
    templateOwnerFilter.value = 'all'
  } else {
    templateOwnerFilter.value = 'all'
  }
  templatePage.value = 1
  handleTemplateSearch()
}

// 解析模板标签
const parseTemplateTags = (tags: any): TemplateTag[] => {
  if (!tags) return []
  if (Array.isArray(tags)) {
    return tags.filter((t: any) => t && typeof t === 'object' && t.id)
  }
  return []
}

// 获取模板平台列表
const fetchTemplatePlatforms = async () => {
  try {
    templatePlatforms.value = await apiClient.getTemplatePlatforms()
  } catch (error: any) {
    console.error('获取模板平台列表失败:', error)
  }
}

// 获取模板标签列表
const fetchTemplateTags = async () => {
  try {
    templateTagsList.value = await apiClient.getTemplateTags()
    templateTags.value = templateTagsList.value.map(t => t.name)
  } catch (error: any) {
    console.error('获取模板标签列表失败:', error)
  }
}

const handleTemplatePageChange = () => {
  handleTemplateSearch()
}

const handleTemplateRowClick = (row: Template) => {
  const isSelected = selectedTemplate.value?.id === row.id
  // 清除之前的选择
  templateTableRef.value?.clearSelection()
  if (isSelected) {
    // 取消选择
    selectedTemplate.value = null
  } else {
    // 勾选当前行
    selectedTemplate.value = row
    templateTableRef.value?.toggleRowSelection(row, true)
  }
}

const handleTemplateSelectionChange = (selection: Template[]) => {
  if (selection.length > 1) {
    templateTableRef.value?.clearSelection()
    templateTableRef.value?.toggleRowSelection(selection[selection.length - 1])
  } else if (selection.length === 1) {
    selectedTemplate.value = selection[0]
  } else {
    selectedTemplate.value = null
  }
}

const templateTableRowClassName = ({ row }: { row: Template }) => {
  return selectedTemplate.value?.id === row.id ? 'selected-row' : ''
}

const clearSelectedTemplate = () => {
  selectedTemplate.value = null
  templateTableRef.value?.clearSelection()
}

// ========== 创作管理员相关 ==========
const loadOperators = async () => {
  try {
    const result = await apiClient.getOperators({ limit: 100 })
    operatorList.value = result?.items || []
    operatorMap.value = {}
    operatorList.value.forEach(op => {
      operatorMap.value[op.id] = op
    })
  } catch (error: any) {
    console.error('加载创作管理员失败:', error)
  }
}

const loadOperatorUserCounts = async () => {
  if (!isSuperAdmin.value) return

  try {
    // 获取所有创作管理员的创作者数量统计
    const counts: Record<number, number> = {}
    for (const operator of operatorList.value) {
      const result = await apiClient.getSubUsers({ operator_id: operator.id, page: 1, limit: 1 })
      counts[operator.id] = result?.total || 0
    }
    operatorUserCounts.value = counts
  } catch (error: any) {
    console.error('加载创作管理员用户统计失败:', error)
  }
}

// 加载创作管理员素材数量统计
const loadOperatorMaterialCounts = async () => {
  if (!isSuperAdmin.value) return

  try {
    const counts: Record<number, number> = {}
    const currentUserId = authStore.user?.id

    // 获取当前超级管理员的素材数量
    const selfResult = await apiClient.getMaterials({ owner_operator_id: currentUserId, page: 1, limit: 1 })
    counts[currentUserId] = selfResult?.total || 0

    // 获取其他创作管理员的素材数量
    for (const operator of operatorList.value) {
      if (operator.id !== currentUserId) {
        const result = await apiClient.getMaterials({ owner_operator_id: operator.id, page: 1, limit: 1 })
        counts[operator.id] = result?.total || 0
      }
    }
    operatorMaterialCounts.value = counts
  } catch (error: any) {
    console.error('加载创作管理员素材统计失败:', error)
  }
}

// 加载创作管理员模板数量统计
const loadOperatorTemplateCounts = async () => {
  if (!isSuperAdmin.value) return

  try {
    const counts: Record<number, number> = {}
    const currentUserId = authStore.user?.id

    // 获取当前超级管理员的模板数量
    const selfResult = await apiClient.getTemplates({ owner_operator_id: currentUserId, page: 1, limit: 1 })
    counts[currentUserId] = selfResult?.total || 0

    // 获取其他创作管理员的模板数量
    for (const operator of operatorList.value) {
      if (operator.id !== currentUserId) {
        const result = await apiClient.getTemplates({ owner_operator_id: operator.id, page: 1, limit: 1 })
        counts[operator.id] = result?.total || 0
      }
    }
    operatorTemplateCounts.value = counts
  } catch (error: any) {
    console.error('加载创作管理员模板统计失败:', error)
  }
}

// ========== 用户标签相关 ==========
const loadUserTags = async () => {
  try {
    const params: any = { tag_type: 'subuser_tag' }

    // 超级管理员：如果选中了创作管理员，加载该创作管理员的标签
    if (isSuperAdmin.value && selectedOperatorId.value) {
      params.operator_id = selectedOperatorId.value
    }

    const tags = await apiClient.getUserTags(params)
    userTagsList.value = tags || []
    // 保持向后兼容
    userTags.value = tags?.map((t: ApiUserTag) => t.name) || []
  } catch (error: any) {
    console.error('获取用户标签失败:', error)
  }
}

// ========== 用户相关 ==========
const handleOperatorClick = (operator: User | null) => {
  selectedOperatorId.value = operator?.id || null
  userTagFilter.value = ''
  userPage.value = 1
  // 重新加载标签和用户
  Promise.all([loadUserTags(), handleUserSearch()])
}

const handleUserSearch = async () => {
  loading.value = true
  try {
    const params: any = {
      page: userPage.value,
      limit: userPageSize.value,
      keyword: userSearch.value || undefined,
      tag_id: userTagFilter.value ? Number(userTagFilter.value) : undefined
    }

    // 超级管理员：使用 selectedOperatorId
    if (isSuperAdmin.value) {
      if (selectedOperatorId.value) {
        params.operator_id = selectedOperatorId.value
      }
    }

    // 同时获取筛选后的用户列表和全部用户数量
    const allParams: any = { page: 1, limit: 1 }
    if (isSuperAdmin.value && selectedOperatorId.value) {
      allParams.operator_id = selectedOperatorId.value
    }

    // 超级管理员还需要获取全局全部用户数量（不受创作管理员筛选影响）
    const globalAllParams: any = { page: 1, limit: 1 }

    const promises: Promise<any>[] = [
      apiClient.getSubUsers(params),
      apiClient.getSubUsers(allParams)
    ]
    if (isSuperAdmin.value) {
      promises.push(apiClient.getSubUsers(globalAllParams))
    }

    const [filteredResult, allUsersResult, globalAllUsersResult] = await Promise.all(promises)

    users.value = filteredResult?.items || []
    usersTotal.value = filteredResult?.total || 0
    allUsersTotal.value = allUsersResult?.total || 0
    if (isSuperAdmin.value && globalAllUsersResult) {
      globalAllUsersTotal.value = globalAllUsersResult?.total || 0
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取创作者列表失败')
  } finally {
    loading.value = false
  }
}

const handleUserPageChange = () => {
  handleUserSearch()
}

const handleUserSelectionChange = (selection: User[]) => {
  selectedUsers.value = selection
}

const handleSelectAllUsers = () => {
  users.value.forEach(user => {
    userTableRef.value?.toggleRowSelection(user, true)
  })
}

const handleCancelSelectUsers = () => {
  userTableRef.value?.clearSelection()
}

// ========== 模型配置 ==========
const fetchModelConfigs = async () => {
  try {
    const configs = await apiClient.getModelConfigs()
    modelConfigs.value = configs || []
  } catch (error: any) {
    console.error('获取模型配置失败:', error)
  }
}

// ========== 步骤导航 ==========
const nextStep = () => {
  // 验证当前步骤
  if (taskMode.value === 'reference') {
    // 对标文案：步骤0-模板创作，步骤1-素材对标，步骤2-模型，步骤3-用户，步骤4-提交
    if (currentStep.value === 0 && !selectedTemplate.value) {
      ElMessage.warning('请选择模板创作')
      return
    }
    if (currentStep.value === 1 && !selectedMaterial.value) {
      ElMessage.warning('请选择素材对标')
      return
    }
    if (currentStep.value === 3 && selectedUsers.value.length === 0) {
      ElMessage.warning('请选择至少一个创作者')
      return
    }
    // 进入素材对标步骤时加载素材对标库列表
    if (currentStep.value === 0) {
      handleBenchmarkMaterialSearch()
    }
    // 进入用户选择步骤时加载用户列表
    if (currentStep.value === 2) {
      handleUserSearch()
    }
    currentStep.value++
  } else if (taskMode.value === 'custom') {
    // 自定义文案：步骤0-模板创作，步骤1-模型，步骤2-用户，步骤3-提交
    if (currentStep.value === 0 && !selectedTemplate.value) {
      ElMessage.warning('请选择模板创作')
      return
    }
    if (currentStep.value === 2 && selectedUsers.value.length === 0) {
      ElMessage.warning('请选择至少一个创作者')
      return
    }
    // 进入用户选择步骤时加载用户列表
    if (currentStep.value === 1) {
      handleUserSearch()
    }
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  } else if (currentStep.value === 0) {
    // 返回模式选择页面，先清空模式再重置步骤
    taskMode.value = null
    materials.value = []
    benchmarkMaterials.value = []
    templates.value = []
    selectedMaterial.value = null
    selectedCreationMaterial.value = null
    selectedTemplate.value = null
    selectedUsers.value = []
    // 最后设置步骤为-1，触发v-if渲染
    currentStep.value = -1
  }
}

const goBack = () => {
  router.push('/generation')
}

// ========== 重置 ==========
const resetForm = () => {
  currentStep.value = -1
  taskMode.value = null
  taskName.value = ''
  selectedMaterial.value = null
  selectedCreationMaterial.value = null
  selectedTemplate.value = null
  selectedUsers.value = []
  modelConfig.model_selection_mode = 'auto'
  modelConfig.llm_model_id = ''
  modelConfig.image_model_id = ''
  modelConfig.video_model_id = ''
  modelConfig.max_concurrency = 5
  modelConfig.image_count = 4
  // 重置对标配置
  benchmarkConfig.text_enabled = true
  benchmarkConfig.image_enabled = true
  benchmarkConfig.image_reference_options = ['composition', 'scene', 'style']
  materialTableRef.value?.clearSelection()
  benchmarkMaterialTableRef.value?.clearSelection()
  templateTableRef.value?.clearSelection()
  userTableRef.value?.clearSelection()
}

// ========== 提交 ==========
const submitTask = async () => {
  // 模板创作验证
  if (!selectedTemplate.value) {
    ElMessage.warning('请选择模板创作')
    return
  }
  // 素材对标（对标库素材）验证 - 仅对标文案模式需要
  if (taskMode.value === 'reference' && !selectedMaterial.value) {
    ElMessage.warning('请选择素材对标')
    return
  }
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('请选择创作者')
    return
  }

  submitting.value = true
  try {
    const requestData: any = {
      sub_user_ids: selectedUsers.value.map(u => u.id),
      model_selection_mode: modelConfig.model_selection_mode,
      max_concurrency: modelConfig.max_concurrency,
      image_count: modelConfig.image_count,
      template_ids: [selectedTemplate.value.id],
    }

    // 添加任务名称（如果有）
    if (taskName.value.trim()) {
      requestData.name = taskName.value.trim()
    }

    // 对标文案模式添加素材对标ID和配置
    if (taskMode.value === 'reference' && selectedMaterial.value) {
      requestData.benchmark_material_id = selectedMaterial.value.id
      requestData.benchmark_text_enabled = benchmarkConfig.text_enabled
      requestData.benchmark_image_enabled = benchmarkConfig.image_enabled
      requestData.benchmark_image_reference_options = benchmarkConfig.image_reference_options
      // V3.0: 图片角色配置（字段名与后端Schema一致）
      if (Object.keys(benchmarkConfig.image_roles).length > 0) {
        requestData.benchmark_image_roles_json = benchmarkConfig.image_roles
      }
      if (Object.keys(benchmarkConfig.product_mapping).length > 0) {
        requestData.template_product_mapping_json = benchmarkConfig.product_mapping
      }
    }

    // 手动模式下添加选定的模型
    if (modelConfig.model_selection_mode === 'manual') {
      // 文本模型
      if (modelConfig.llm_model_id) {
        const selectedModel = llmModels.value.find(m => m.id === Number(modelConfig.llm_model_id))
        if (selectedModel) {
          requestData.model_platform = selectedModel.platform
          requestData.model_id = selectedModel.model_id
        }
      }
      // 图片模型
      if (modelConfig.image_model_id) {
        const selectedImageModel = imageModels.value.find(m => m.id === Number(modelConfig.image_model_id))
        if (selectedImageModel) {
          requestData.image_model_platform = selectedImageModel.platform
          requestData.image_model_id = selectedImageModel.model_id
        }
      }
    }

    // 文案去重配置（根据 scope 是否有值来设置 enabled）
    if (modelConfig.dedup_scope && modelConfig.dedup_scope.length > 0) {
      requestData.dedup_enabled = true
      requestData.dedup_scope = modelConfig.dedup_scope
      // 使用后端默认阈值 90% 和重试次数 3 次
    } else {
      requestData.dedup_enabled = false
    }

    // 图片去重配置（根据 scope 是否有值来设置 enabled）
    if (modelConfig.image_dedup_scope && modelConfig.image_dedup_scope.length > 0) {
      requestData.image_dedup_enabled = true
      requestData.image_dedup_scope = modelConfig.image_dedup_scope
      // 使用后端默认阈值 90% 和重试次数 3 次
    } else {
      requestData.image_dedup_enabled = false
    }

    const newTask = await apiClient.createGenerationTask(requestData)
    ElMessage.success('任务创建成功！')
    // 记录操作日志
    await logOperation({
      module: MODULE_GENERATION,
      action: 'create',
      description: `创建生成任务：${taskName.value || `任务 #${newTask?.id}`}`,
      table_name: 'generation_task',
      record_id: newTask?.id,
      new_value: {
        name: taskName.value || null,
        template_id: selectedTemplate.value?.id,
        sub_user_count: selectedUsers.value.length,
        model_selection_mode: modelConfig.model_selection_mode,
        max_concurrency: modelConfig.max_concurrency
      }
    })
    router.push('/generation')
  } catch (error: any) {
    ElMessage.error(error.message || '创建任务失败')
  } finally {
    submitting.value = false
  }
}

// ========== 工具函数 ==========
const getContentTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    text: '纯文本',
    image_text: '图文',
    video_text: '视频文字'
  }
  return labels[type] || type
}

const getContentTypeTag = (type: string) => {
  const tags: Record<string, string> = {
    text: '',
    image_text: 'success',
    video_text: 'warning'
  }
  return tags[type] || 'info'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

// 解析标签（支持字符串或对象数组）
const parseTags = (tags: any): string[] => {
  if (!tags) return []
  if (Array.isArray(tags)) {
    // 如果是对象数组，提取name字段
    return tags.map((t: any) => typeof t === 'string' ? t : (t.name || '')).filter(Boolean)
  }
  if (typeof tags === 'string') {
    return tags.split(',').filter(Boolean)
  }
  return []
}

// 解析用户标签（返回完整标签对象数组）
const parseUserTags = (tags: any): ApiUserTag[] => {
  if (!tags) return []
  if (Array.isArray(tags)) {
    return tags.filter((t: any) => t && typeof t === 'object' && t.id)
  }
  return []
}

// 计算标签样式，确保文字颜色与背景色对比度足够
const getTagStyle = (color: string | undefined) => {
  if (!color) {
    return {
      backgroundColor: '#8B7CF6',
      color: '#ffffff'
    }
  }

  // 移除 # 前缀（如果有）
  let hex = color.replace('#', '')

  // 处理短格式颜色（3位）
  if (hex.length === 3) {
    hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2]
  }

  // 解析RGB值
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)

  // 计算相对亮度（使用W3C公式）
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

  // 根据亮度选择文字颜色（亮度>0.5使用深色，否则使用白色）
  const textColor = luminance > 0.5 ? '#303133' : '#ffffff'

  return {
    backgroundColor: color,
    color: textColor,
    borderColor: color
  }
}

// ========== 初始化 ==========
onMounted(() => {
  // 超级管理员不能创建任务
  if (isSuperAdmin.value) {
    ElMessage.warning('超级管理员不能创建生成任务，请由创作管理员操作')
    router.push('/generation/list')
    return
  }

  fetchModelConfigs()
  fetchMaterialTags()
  fetchMaterialPlatforms()
  fetchTemplatePlatforms()
  fetchTemplateTags()
  loadPlatformModelTypes()

  // 初始化标签列表（可从后端获取）
  userTags.value = ['活跃', '新用户', 'VIP', '潜力']

  // 加载用户标签
  loadUserTags()
})
</script>

<style lang="scss" scoped>
.generation-create-view {
  padding: 0;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 180px);
}

.card {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: visible;
}

.step-content {
  flex: 1;
  overflow-y: auto;
}

.mb-lg {
  margin-bottom: 24px;
}

.mt-md {
  margin-top: 16px;
}

.mt-lg {
  margin-top: 24px;
}

.my-lg {
  margin-top: 24px;
  margin-bottom: 24px;
}

.mr-xs {
  margin-right: 4px;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.step-title {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 20px;
}

.text-muted {
  color: var(--text-placeholder);
  font-size: 13px;
}

// 模式选择卡片
.mode-selection {
  display: flex;
  gap: 24px;
  justify-content: center;
  padding: 40px 0;

  .mode-card {
    width: 320px;
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(64, 158, 255, 0.2);
    }

    .mode-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
      padding: 20px;

      h4 {
        margin: 0;
        font-size: 18px;
        color: var(--text-primary);
      }

      p {
        margin: 0;
        color: var(--text-placeholder);
        font-size: 14px;
        text-align: center;
      }
    }
  }
}

// 工具栏
.selector-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

// 分页
.pagination-wrapper {
  margin-top: $spacing-md;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: $spacing-sm 0;
  border-top: 1px solid var(--color-border-default);
}

// 选中预览
.selected-preview {
  margin-top: 16px;
}

// 预估信息
.estimate-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 4px;
  color: var(--color-primary);
  font-size: 14px;

  .el-icon {
    font-size: 16px;
  }

  .estimate-text {
    strong {
      font-size: 15px;
    }
  }
}

.estimate-card {
  .card-header {
    font-weight: 500;
  }

  .estimate-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;

    .label {
      color: var(--text-muted);
      font-size: 14px;
    }

    .value {
      font-weight: 500;
      font-size: 14px;

      &.highlight {
        color: var(--color-primary);
        font-size: 16px;
        font-weight: 600;
      }
    }
  }
}

.selected-summary {
  font-size: 14px;
  color: var(--text-secondary);
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-radius: 4px;
}

.confirmation-summary {
  max-width: 800px;
}

.task-name-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

// 表格选中行样式
:deep(.selected-row) {
  background-color: rgba(64, 158, 255, 0.1) !important;
}

// 步骤操作按钮区域 - 固定在底部
.step-actions {
  position: sticky;
  bottom: 0;
  background: var(--bg-primary);
  padding: 16px 0;
  margin-top: 0 !important;
  border-top: 1px solid var(--border-color);
  z-index: 10;
}

// 分类面板样式
.category-panel {
  height: calc(100vh - 280px);
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

.category-list {
  .category-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-radius: 4px;
    cursor: pointer;
    margin-bottom: 4px;
    transition: background-color 0.2s;

    &:hover {
      background-color: var(--bg-tertiary);
    }

    &.active {
      background-color: rgba(64, 158, 255, 0.15);
      color: var(--color-primary);
    }

    .category-name {
      flex: 1;
    }

    .category-count {
      color: var(--text-placeholder);
      font-size: 13px;
      margin-left: 4px;
    }
  }
}

// 自定义树节点样式
.custom-tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 8px;
}

.node-label {
  flex: 1;
}

// 图片角色配置样式
.image-role-config {
  margin-top: 12px;
  padding: 12px;
  background-color: var(--bg-tertiary);
  border-radius: 6px;
  border: 1px solid var(--border-color);

  .role-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 10px 12px;
    background-color: var(--bg-primary);
    border-radius: 4px;
    margin-bottom: 8px;
    border: 1px solid var(--border-color);

    &:last-child {
      margin-bottom: 0;
    }

    .role-item-header {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 140px;
    }

    .role-item-label {
      font-weight: 500;
      color: var(--text-primary);
      font-size: 14px;
    }

    .role-checkbox-group {
      flex: 1;
      display: flex;
      gap: 16px;
    }
  }
}

// 产品映射配置样式
.product-mapping-config {
  margin-top: 12px;
  padding: 12px;
  background-color: var(--bg-tertiary);
  border-radius: 6px;
  border: 1px solid var(--border-color);

  .mapping-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 10px 12px;
    background-color: var(--bg-primary);
    border-radius: 4px;
    margin-bottom: 8px;
    border: 1px solid var(--border-color);

    &:last-child {
      margin-bottom: 0;
    }

    .mapping-item-header {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 140px;
    }

    .mapping-item-label {
      font-weight: 500;
      color: var(--text-primary);
      font-size: 14px;
    }
  }
}
</style>
