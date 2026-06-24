<template>
  <div class="distribute-view">
    <h2 class="page-title">内容分发</h2>

    <el-row :gutter="20">
      <el-col :span="12">
        <div class="card">
          <h3 class="section-title">选择生成内容</h3>
          <div class="task-selector mb-md">
            <el-select v-model="selectedTask" placeholder="选择生成任务" style="width: 100%;">
              <el-option label="T20240326002 - 抖音产品推广文案生成" value="task2" />
              <el-option label="T20240325001 - 母婴好物推荐内容生成" value="task1" />
            </el-select>
          </div>
          <div class="content-list">
            <el-table
              :data="contents"
              @selection-change="handleContentSelection"
              style="width: 100%;"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column prop="id" label="内容ID" width="100" />
              <el-table-column prop="title" label="标题" show-overflow-tooltip />
              <el-table-column prop="subUserName" label="目标用户" width="120" />
              <el-table-column label="预览" width="80">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="openPreview(row)">预览</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div class="selection-summary mt-md">
            已选择 <strong>{{ selectedContents.length }}</strong> 条内容
          </div>
        </div>
      </el-col>

      <el-col :span="12">
        <div class="card">
          <h3 class="section-title">选择目标创作者</h3>
          <div class="category-select mb-md">
            <el-checkbox-group v-model="selectedCategories">
              <el-checkbox label="xiaohongshu-meizhuang">小红书美妆</el-checkbox>
              <el-checkbox label="xiaohongshu-muying">小红书母婴</el-checkbox>
              <el-checkbox label="douyin-tuangou">抖音团购</el-checkbox>
            </el-checkbox-group>
          </div>
          <el-divider />
          <div class="user-list">
            <el-table
              :data="users"
              @selection-change="handleUserSelection"
              style="width: 100%;"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column prop="id" label="用户ID" width="100" />
              <el-table-column prop="nickname" label="昵称" width="140" />
              <el-table-column prop="categories" label="分类">
                <template #default="{ row }">
                  <el-tag v-for="cat in row.categories" :key="cat" size="small" style="margin-right: 4px;">
                    {{ cat }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
                    {{ row.status === 'active' ? '正常' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div class="selection-summary mt-md">
            已选择 <strong>{{ selectedUsers.length }}</strong> 个创作者
          </div>
        </div>
      </el-col>
    </el-row>

    <div class="card mt-lg">
      <h3 class="section-title">分发确认</h3>
      <el-alert
        title="分发预览"
        type="info"
        :closable="false"
        class="mb-md"
      >
        <template #default>
          <p>将向 <strong>{{ selectedUsers.length }}</strong> 个创作者分发 <strong>{{ selectedContents.length }}</strong> 条内容</p>
          <p>每个创作者将收到差异化的内容版本</p>
        </template>
      </el-alert>
      <div class="distribute-actions flex-center">
        <el-button size="large" @click="resetSelection">重置选择</el-button>
        <el-button type="primary" size="large" :loading="distributing" @click="handleDistribute">
          确认分发
        </el-button>
      </div>
    </div>

    <el-dialog v-model="showPreview" title="内容预览" width="600px">
      <div class="content-preview">
        <h4>{{ previewContent?.title }}</h4>
        <div class="preview-text">{{ previewContent?.text }}</div>
        <div class="preview-images mt-md" v-if="previewContent?.images?.length">
          <el-image
            v-for="(img, idx) in previewContent.images"
            :key="idx"
            :src="img"
            fit="cover"
            class="preview-image"
          />
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="copyContent">复制文案</el-button>
        <el-button type="success" @click="downloadImages">下载图片</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const selectedTask = ref('')
const selectedCategories = ref<string[]>([])
const selectedContents = ref<any[]>([])
const selectedUsers = ref<any[]>([])
const distributing = ref(false)
const showPreview = ref(false)
const previewContent = ref<any>(null)

const contents = ref([
  { id: 'C001', title: '这款美妆产品真的超级好用！', subUserName: '小美同学' },
  { id: 'C002', title: '今日推荐：神仙水的正确打开方式', subUserName: '美妆博主' },
  { id: 'C003', title: '手把手教你画日常妆容', subUserName: '时尚达人' },
  { id: 'C004', title: '这5款美妆产品无限回购', subUserName: '种草小能手' }
])

const users = ref([
  { id: 'U001', nickname: '小美同学', categories: ['小红书美妆'], status: 'active' },
  { id: 'U002', nickname: '美妆博主', categories: ['小红书美妆'], status: 'active' },
  { id: 'U003', nickname: '母婴达人', categories: ['小红书母婴'], status: 'active' },
  { id: 'U004', nickname: '团购小哥', categories: ['抖音团购'], status: 'active' }
])

const handleContentSelection = (selection: any[]) => {
  selectedContents.value = selection
}

const handleUserSelection = (selection: any[]) => {
  selectedUsers.value = selection
}

const openPreview = (row: any) => {
  previewContent.value = {
    title: row.title,
    text: '这是生成的正文内容，包含了产品介绍、使用心得等详细信息...',
    images: ['', '', '']
  }
  showPreview.value = true
}

const copyContent = () => {
  ElMessage.success('文案已复制到剪贴板')
}

const downloadImages = () => {
  ElMessage.success('图片下载已开始')
}

const resetSelection = () => {
  selectedContents.value = []
  selectedUsers.value = []
  selectedCategories.value = []
  ElMessage.info('已重置选择')
}

const handleDistribute = async () => {
  if (selectedContents.value.length === 0 || selectedUsers.value.length === 0) {
    ElMessage.warning('请选择内容和目标用户')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要向 ${selectedUsers.value.length} 个创作者分发 ${selectedContents.value.length} 条内容吗？`,
      '确认分发',
      { type: 'warning' }
    )

    distributing.value = true
    await new Promise(resolve => setTimeout(resolve, 1500))
    ElMessage.success('分发成功！')
  } catch {
    // User cancelled
  } finally {
    distributing.value = false
  }
}
</script>

<style lang="scss" scoped>
.distribute-view {
  padding: 0;
}

.mb-md {
  margin-bottom: 16px;
}

.mt-md {
  margin-top: 16px;
}

.mt-lg {
  margin-top: 24px;
}

.flex-center {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 16px;
}

.selection-summary {
  font-size: 14px;
  color: #606266;
}

.distribute-actions {
  padding-top: 16px;
}

.content-preview {
  h4 {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 16px;
  }
  .preview-text {
    color: #606266;
    line-height: 1.8;
  }
  .preview-images {
    display: flex;
    gap: 12px;
    .preview-image {
      width: 100px;
      height: 100px;
      border-radius: 4px;
      background: #f5f7fa;
    }
  }
}
</style>
