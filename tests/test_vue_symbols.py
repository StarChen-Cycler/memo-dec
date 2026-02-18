#!/usr/bin/env python3
"""Unit tests for Vue symbol extraction"""

import sys
from pathlib import Path
import unittest

# Add parent directory to path to import memo_dec
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols, extract_symbols_from_directory


class TestVueSymbolExtraction(unittest.TestCase):
    """Test Vue single-file component symbol extraction"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(__file__).parent / "vue_test_files"
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test files"""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_vue_component_with_script_setup(self):
        """Test Vue 3 Composition API with <script setup>"""
        vue_content = '''<template>
  <div class="user-profile">
    <h2>{{ userName }}</h2>
    <button @click="updateProfile">Update</button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const userName = ref('John Doe')
const userAge = ref(25)

const userInfo = computed(() => {
  return `${userName.value} - ${userAge.value} years old`
})

function updateProfile() {
  console.log('Updating profile...')
}

const resetData = () => {
  userName.value = ''
  userAge.value = 0
}
</script>

<style scoped>
.user-profile {
  padding: 20px;
}
</style>
'''

        test_file = self.test_dir / "UserProfile.vue"
        test_file.write_text(vue_content, encoding='utf-8')

        symbols = extract_symbols(test_file)

        # Should extract template tags
        template_tags = [s for s in symbols if s['type'] == 'tag']
        tag_names = [s['name'] for s in template_tags]
        self.assertIn('div', tag_names)
        self.assertIn('h2', tag_names)
        self.assertIn('button', tag_names)

        # Should extract attributes
        attributes = [s for s in symbols if s['type'] == 'attribute']
        attr_names = [s['name'] for s in attributes]
        # The HTML parser combines attribute name and value
        self.assertTrue(any('class' in attr for attr in attr_names))
        self.assertTrue(any('@click' in attr for attr in attr_names))

    def test_vue_options_api(self):
        """Test Vue 2/3 Options API"""
        vue_content = '''<template>
  <div>
    <p>Count: {{ count }}</p>
    <button @click="increment">Increment</button>
  </div>
</template>

<script>
export default {
  name: 'CounterComponent',
  data() {
    return {
      count: 0,
      message: 'Hello'
    }
  },
  computed: {
    doubled() {
      return this.count * 2
    }
  },
  methods: {
    increment() {
      this.count++
    },
    decrement() {
      this.count--
    }
  },
  mounted() {
    console.log('Component mounted')
  }
}
</script>
'''

        test_file = self.test_dir / "Counter.vue"
        test_file.write_text(vue_content, encoding='utf-8')

        symbols = extract_symbols(test_file)

        # Extract template tags
        template_tags = [s for s in symbols if s['type'] == 'tag']
        tag_names = [s['name'] for s in template_tags]
        self.assertIn('div', tag_names)
        self.assertIn('p', tag_names)
        self.assertIn('button', tag_names)

    def test_vue_composition_api_separate_script(self):
        """Test Vue 3 Composition API with separate <script>"""
        vue_content = '''<template>
  <div class="todo-list">
    <input v-model="newTodo" @keyup.enter="addTodo" />
    <ul>
      <li v-for="todo in todos" :key="todo.id">
        {{ todo.text }}
      </li>
    </ul>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  setup() {
    const todos = ref([])
    const newTodo = ref('')

    const addTodo = () => {
      if (newTodo.value.trim()) {
        todos.value.push({
          id: Date.now(),
          text: newTodo.value
        })
        newTodo.value = ''
      }
    }

    return {
      todos,
      newTodo,
      addTodo
    }
  }
}
</script>
'''

        test_file = self.test_dir / "TodoList.vue"
        test_file.write_text(vue_content, encoding='utf-8')

        symbols = extract_symbols(test_file)

        # Check template tags
        template_tags = [s for s in symbols if s['type'] == 'tag']
        tag_names = [s['name'] for s in template_tags]
        self.assertIn('div', tag_names)
        self.assertIn('input', tag_names)
        self.assertIn('ul', tag_names)
        self.assertIn('li', tag_names)

        # Check attributes including Vue directives
        attributes = [s for s in symbols if s['type'] == 'attribute']
        attr_names = [s['name'] for s in attributes]
        # The HTML parser combines attribute name and value
        self.assertTrue(any('class' in attr for attr in attr_names))
        self.assertTrue(any('v-model' in attr for attr in attr_names))
        self.assertTrue(any('@keyup.enter' in attr for attr in attr_names))
        self.assertTrue(any('v-for' in attr for attr in attr_names))
        self.assertTrue(any(':key' in attr for attr in attr_names))

    def test_vue_with_nested_components(self):
        """Test Vue component with nested custom components"""
        vue_content = '''<template>
  <div class="app">
    <Header />
    <main>
      <Sidebar :items="menuItems" />
      <Content>
        <router-view />
      </Content>
    </main>
    <Footer />
  </div>
</template>

<script setup>
import Header from './components/Header.vue'
import Sidebar from './components/Sidebar.vue'
import Content from './components/Content.vue'
import Footer from './components/Footer.vue'

const menuItems = [
  { id: 1, label: 'Home' },
  { id: 2, label: 'About' }
]
</script>
'''

        test_file = self.test_dir / "App.vue"
        test_file.write_text(vue_content, encoding='utf-8')

        symbols = extract_symbols(test_file)

        # Extract custom component tags
        template_tags = [s for s in symbols if s['type'] == 'tag']
        tag_names = [s['name'] for s in template_tags]
        self.assertIn('div', tag_names)
        self.assertIn('main', tag_names)
        # Custom components should also be extracted as tags
        self.assertIn('Header', tag_names)
        self.assertIn('Sidebar', tag_names)
        self.assertIn('Content', tag_names)
        self.assertIn('Footer', tag_names)

    def test_vue_directives_and_attributes(self):
        """Test Vue-specific directives and bindings"""
        vue_content = '''<template>
  <div
    v-if="isVisible"
    v-show="showDiv"
    :class="dynamicClass"
    :style="computedStyle"
    @click="handleClick"
    @mouseenter="handleHover"
    v-model="inputValue"
  >
    <p v-text="message"></p>
    <p v-html="htmlContent"></p>
    <CustomComponent
      :prop-name="value"
      @custom-event="eventHandler"
      v-slot="slotProps"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const isVisible = ref(true)
const showDiv = ref(false)
const inputValue = ref('')
const message = ref('Hello')
const htmlContent = ref('<strong>Bold</strong>')

const dynamicClass = computed(() => ({
  active: isVisible.value,
  hidden: !showDiv.value
}))

const computedStyle = computed(() => ({
  color: 'red',
  fontSize: '16px'
}))

const handleClick = () => {
  console.log('Clicked')
}

const handleHover = () => {
  console.log('Hovered')
}

const value = ref('test')

const eventHandler = (payload) => {
  console.log('Event:', payload)
}

const slotProps = ref({ data: 'test' })
</script>
'''

        test_file = self.test_dir / "DirectivesTest.vue"
        test_file.write_text(vue_content, encoding='utf-8')

        symbols = extract_symbols(test_file)

        # Extract all attributes
        attributes = [s for s in symbols if s['type'] == 'attribute']
        attr_names = [s['name'] for s in attributes]

        # Check for Vue directives (HTML parser returns full attribute text)
        self.assertTrue(any(':class' in attr for attr in attr_names))
        self.assertTrue(any(':style' in attr for attr in attr_names))
        self.assertTrue(any('@click' in attr for attr in attr_names))
        self.assertTrue(any('@mouseenter' in attr for attr in attr_names))
        self.assertTrue(any('v-model' in attr for attr in attr_names))
        self.assertTrue(any('v-if' in attr for attr in attr_names))
        self.assertTrue(any('v-show' in attr for attr in attr_names))
        self.assertTrue(any('v-text' in attr for attr in attr_names))
        self.assertTrue(any('v-html' in attr for attr in attr_names))
        self.assertTrue(any(':prop-name' in attr for attr in attr_names))
        self.assertTrue(any('@custom-event' in attr for attr in attr_names))
        self.assertTrue(any('v-slot' in attr for attr in attr_names))

    def test_empty_vue_file(self):
        """Test handling of empty or minimal Vue files"""
        vue_content = '<template></template>'

        test_file = self.test_dir / "Empty.vue"
        test_file.write_text(vue_content, encoding='utf-8')

        symbols = extract_symbols(test_file)

        # Should handle gracefully and return empty list or minimal symbols
        self.assertIsInstance(symbols, list)

    def test_extract_symbols_from_directory(self):
        """Test extracting symbols from multiple Vue files in directory"""
        # Create multiple test files
        files = [
            ("Component1.vue", "<template><div>Comp1</div></template>"),
            ("Component2.vue", "<template><span>Comp2</span></template>"),
            ("Component3.vue", "<template><p>Comp3</p></template>")
        ]

        for filename, content in files:
            test_file = self.test_dir / filename
            test_file.write_text(content, encoding='utf-8')

        symbols = extract_symbols_from_directory(self.test_dir)

        # Should extract symbols from all files
        self.assertGreater(len(symbols), 0)

        # Check that symbols have correct structure
        for symbol in symbols:
            self.assertIn('file', symbol)
            self.assertIn('line', symbol)
            self.assertIn('type', symbol)
            self.assertIn('name', symbol)


if __name__ == '__main__':
    unittest.main()
