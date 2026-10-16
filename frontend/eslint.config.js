import js from '@eslint/js'
import globals from 'globals'
import hooks from 'eslint-plugin-react-hooks'
import react from 'eslint-plugin-react-x'

export default [
  { ignores: ['dist/**', 'node_modules/**'] },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest', sourceType: 'module',
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: { ...globals.browser, ...globals.node },
    },
    plugins: { 'react-hooks': hooks, 'react-x': react },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'error',
      'react-x/no-missing-key': 'error',
      'react-x/no-duplicate-key': 'error',
    },
  },
]
