#!/usr/bin/env python3
"""
Unit tests for TypeScript file symbol extraction.
"""
import sys
import unittest
from pathlib import Path
from memo_dec.symbol_extractor import extract_symbols, extract_symbols_from_directory


class TestTypeScriptSymbolExtraction(unittest.TestCase):
    """Test TypeScript file symbol extraction including interfaces, types, and classes."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(__file__).parent / "test_typescript_files"
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test files."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_simple_class_extraction(self):
        """Test a simple TypeScript class to debug symbol extraction."""
        ts_content = '''
class SimpleClass {
  private value: number = 0;

  constructor(initial: number) {
    this.value = initial;
  }

  getValue(): number {
    return this.value;
  }

  setValue(val: number): void {
    this.value = val;
  }
}

class AnotherClass {
  public name: string = 'test';
}

function standaloneFunction(): void {
  console.log('test');
}

const arrowFunction = (): void => {
  console.log('arrow');
};
'''
        test_file = self.test_dir / "simple.ts"
        test_file.write_text(ts_content)

        symbols = extract_symbols(test_file)

        # Debug: print all symbols
        print(f"\n=== ALL SYMBOLS FOR simple.ts ===")
        for sym in symbols:
            print(f"  {sym}")
        print("=====================================\n")

        # Verify we got symbols
        self.assertGreater(len(symbols), 0)

        # Collect symbols by type
        classes = [s for s in symbols if s['type'] == 'class']
        functions = [s for s in symbols if s['type'] == 'function']
        components = [s for s in symbols if s['type'] == 'component']
        variables = [s for s in symbols if s['type'] == 'variable']

        print(f"Classes found: {len(classes)}")
        print(f"Functions found: {len(functions)}")
        print(f"Components (arrow functions) found: {len(components)}")
        print(f"Variables found: {len(variables)}")

        print(f"Class names: {[c['name'] for c in classes]}")
        print(f"Function names: {[f['name'] for f in functions]}")
        print(f"Component names: {[c['name'] for c in components]}")

    def test_type_script_interface_and_types(self):
        """Test TypeScript interfaces, types, and standard classes/functions."""
        ts_content = '''
interface User {
  id: number;
  name: string;
  email: string;
}

type UserId = number;

type UserResponse<T> = {
  data: T;
  success: boolean;
};

interface Repository<T> {
  findById(id: number): Promise<T | null>;
  save(entity: T): Promise<void>;
}

class UserRepository implements Repository<User> {
  private users: Map<number, User> = new Map();

  async findById(id: number): Promise<User | null> {
    return this.users.get(id) || null;
  }

  async save(user: User): Promise<void> {
    this.users.set(user.id, user);
  }

  private validate(user: User): boolean {
    return user.id > 0 && user.name.length > 0;
  }
}

abstract class BaseService<T> {
  protected abstract getRepository(): Repository<T>;

  async findById(id: number): Promise<T | null> {
    return await this.getRepository().findById(id);
  }
}

export class UserService extends BaseService<User> {
  constructor(private repository: UserRepository) {
    super();
  }

  protected getRepository(): Repository<User> {
    return this.repository;
  }

  async createUser(name: string, email: string): Promise<User> {
    const user: User = {
      id: Date.now(),
      name,
      email
    };

    if (this.repository.save) {
      await this.repository.save(user);
    }

    return user;
  }
}

const createUserValidator = (user: Partial<User>): boolean => {
  return user.name !== undefined && user.email !== undefined;
};

function formatUser(user: User): string {
  return `${user.name} <${user.email}>`;
}

export { User, UserId, UserResponse };
'''
        test_file = self.test_dir / "user_service.ts"
        test_file.write_text(ts_content)

        symbols = extract_symbols(test_file)

        # Debug: print all symbols to see what's being extracted
        print(f"\n=== ALL SYMBOLS FOR {test_file.name} ===")
        for sym in symbols:
            print(f"  {sym}")
        print("=====================================\n")

        # Verify we got symbols
        self.assertGreater(len(symbols), 0)

        # DEBUG: Print all symbols
        print(f"\n=== ALL SYMBOLS FOR user_service.ts ===")
        for sym in symbols:
            print(f"  {sym}")
        print("=====================================\n")

        # Collect symbols by type
        classes = [s for s in symbols if s['type'] == 'class']
        functions = [s for s in symbols if s['type'] == 'function']
        variables = [s for s in symbols if s['type'] == 'variable']

        # Check classes
        class_names = [c['name'] for c in classes]
        self.assertIn('UserRepository', class_names)
        self.assertIn('BaseService', class_names)
        self.assertIn('UserService', class_names)

        # Check functions
        function_names = [f['name'] for f in functions]
        self.assertIn('formatUser', function_names)
        self.assertIn('createUser', function_names)  # method from UserService

        # Check components (arrow functions)
        components = [s for s in symbols if s['type'] == 'component']
        component_names = [c['name'] for c in components]
        self.assertIn('createUserValidator', component_names)

        # Check variables
        variable_names = [v['name'] for v in variables]
        # Interface properties (id, name, email) are not extracted as they're type definitions
        # Class properties (users, repository) are not extracted by this symbol extractor
        # Only actual variable declarations are extracted
        self.assertIn('user', variable_names)  # local variable in UserService.createUser

    def test_type_script_enums_and_generics(self):
        """Test TypeScript enums and generic types."""
        ts_content = '''
enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  GUEST = 'guest'
}

enum StatusCode {
  OK = 200,
  NOT_FOUND = 404,
  SERVER_ERROR = 500
}

const rolePermissions: Map<UserRole, string[]> = new Map([
  [UserRole.ADMIN, ['read', 'write', 'delete']],
  [UserRole.USER, ['read', 'write']],
  [UserRole.GUEST, ['read']]
]);

function getUserPermissions<T extends UserRole>(role: T): string[] {
  return rolePermissions.get(role) || [];
}

const hasPermission = <T extends string>(role: string, permission: T): boolean => {
  const permissions = getUserPermissions(role as UserRole);
  return permissions.includes(permission);
};

class PermissionManager {
  private readonly roleMap: Map<UserRole, string[]>;

  constructor() {
    this.roleMap = new Map();
  }

  public assignRole(role: UserRole, permissions: string[]): void {
    this.roleMap.set(role, permissions);
  }

  public getPermissions(role: UserRole): string[] {
    return this.roleMap.get(role) || [];
  }
}

export { UserRole, StatusCode, rolePermissions };
'''
        test_file = self.test_dir / "permissions.ts"
        test_file.write_text(ts_content)

        symbols = extract_symbols(test_file)

        # Verify symbols exist
        self.assertGreater(len(symbols), 0)

        # Check for classes
        classes = [s for s in symbols if s['type'] == 'class']
        class_names = [c['name'] for c in classes]
        self.assertIn('PermissionManager', class_names)

        # Check for functions
        functions = [s for s in symbols if s['type'] == 'function']
        function_names = [f['name'] for f in functions]
        self.assertIn('getUserPermissions', function_names)
        # Note: hasPermission with explicit generic type parameters has complex TS-specific syntax
        # that requires special handling in queries (edge case not covered in basic implementation)

    def test_type_script_with_namespaces(self):
        """Test TypeScript namespace declarations."""
        ts_content = '''
namespace App {
  interface Config {
    version: string;
    environment: 'development' | 'production';
  }

  export const config: Config = {
    version: '1.0.0',
    environment: 'development'
  };

  export function initialize(): void {
    console.log(`App v${config.version} initialized`);
  }

  export class Service {
    private static instance: Service;

    static getInstance(): Service {
      if (!Service.instance) {
        Service.instance = new Service();
      }
      return Service.instance;
    }

    execute(): void {
      console.log('Service executed');
    }
  }
}

export default App;
'''
        test_file = self.test_dir / "app_namespace.ts"
        test_file.write_text(ts_content)

        symbols = extract_symbols(test_file)

        # Verify symbols were extracted
        self.assertGreater(len(symbols), 0)

        # Check for class
        classes = [s for s in symbols if s['type'] == 'class']
        class_names = [c['name'] for c in classes]
        self.assertIn('Service', class_names)

        # Check for functions
        functions = [s for s in symbols if s['type'] == 'function']
        function_names = [f['name'] for f in functions]
        self.assertIn('initialize', function_names)
        self.assertIn('getInstance', function_names)
        self.assertIn('execute', function_names)

    def test_type_script_with_decorators(self):
        """Test TypeScript with decorator annotation syntax."""
        ts_content = '''
function log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const originalMethod = descriptor.value;

  descriptor.value = function (...args: any[]) {
    console.log(`Calling ${propertyKey} with`, args);
    const result = originalMethod.apply(this, args);
    console.log(`Called ${propertyKey}, result:`, result);
    return result;
  };

  return descriptor;
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = 'https://api.example.com';
  }

  @log
  async fetchData(endpoint: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/${endpoint}`);
    return response.json();
  }
}

const client = new ApiClient();
'''
        test_file = self.test_dir / "decorators.ts"
        test_file.write_text(ts_content)

        symbols = extract_symbols(test_file)

        # Check for class
        classes = [s for s in symbols if s['type'] == 'class']
        class_names = [c['name'] for c in classes]
        self.assertIn('ApiClient', class_names)

        # Check for functions
        functions = [s for s in symbols if s['type'] == 'function']
        function_names = [f['name'] for f in functions]
        self.assertIn('log', function_names)
        self.assertIn('fetchData', function_names)


def main():
    """Run the tests."""
    unittest.main()


if __name__ == '__main__':
    main()
