import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu, ConfigProvider, theme } from 'antd';
import {
  DashboardOutlined,
  ShoppingOutlined,
  LineChartOutlined,
  FileTextOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Reports from './pages/Reports';
import Trends from './pages/Trends';
import './App.css';

const { Header, Sider, Content } = Layout;

const AppLayout = () => {
  const location = useLocation();

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: <Link to="/">Dashboard</Link> },
    { key: '/products', icon: <ShoppingOutlined />, label: <Link to="/products">Products</Link> },
    { key: '/trends', icon: <LineChartOutlined />, label: <Link to="/trends">Trends</Link> },
    { key: '/reports', icon: <FileTextOutlined />, label: <Link to="/reports">Reports</Link> },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" width={220} style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #f0f0f0' }}>
          <h2 style={{ margin: 0, fontSize: 18 }}>AU/NZ Finder</h2>
          <span style={{ color: '#999', fontSize: 12 }}>Product Selection Tool</span>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 16, fontWeight: 500 }}>
            {location.pathname === '/' && 'Dashboard'}
            {location.pathname === '/products' && 'Product Search'}
            {location.pathname === '/trends' && 'Google Trends'}
            {location.pathname === '/reports' && 'Reports'}
          </span>
          <SettingOutlined style={{ fontSize: 18, cursor: 'pointer' }} />
        </Header>
        <Content style={{ background: '#f5f5f5', minHeight: 280 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/products" element={<Products />} />
            <Route path="/trends" element={<Trends />} />
            <Route path="/reports" element={<Reports />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

function App() {
  return (
    <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
