import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu, ConfigProvider, theme, Dropdown, Button } from 'antd';
import {
  DashboardOutlined,
  ShoppingOutlined,
  LineChartOutlined,
  FileTextOutlined,
  GlobalOutlined,
  ShopOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Reports from './pages/Reports';
import Trends from './pages/Trends';
import Suppliers from './pages/Suppliers';
import './App.css';

const { Header, Sider, Content } = Layout;

const AppLayout = () => {
  const location = useLocation();
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  const languageItems = [
    { key: 'en', label: 'English', onClick: () => changeLanguage('en') },
    { key: 'zh', label: '中文', onClick: () => changeLanguage('zh') },
  ];

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: <Link to="/">{t('nav.dashboard')}</Link> },
    { key: '/products', icon: <ShoppingOutlined />, label: <Link to="/products">{t('nav.products')}</Link> },
    { key: '/suppliers', icon: <ShopOutlined />, label: <Link to="/suppliers">1688供应商</Link> },
    { key: '/trends', icon: <LineChartOutlined />, label: <Link to="/trends">{t('nav.trends')}</Link> },
    { key: '/reports', icon: <FileTextOutlined />, label: <Link to="/reports">{t('nav.reports')}</Link> },
  ];

  const getHeaderTitle = () => {
    switch (location.pathname) {
      case '/': return t('header.dashboard');
      case '/products': return t('header.productSearch');
      case '/suppliers': return '1688供应商数据库';
      case '/trends': return t('header.googleTrends');
      case '/reports': return t('header.reports');
      default: return '';
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" width={220} style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #f0f0f0' }}>
          <h2 style={{ margin: 0, fontSize: 18 }}>{t('app.title')}</h2>
          <span style={{ color: '#999', fontSize: 12 }}>{t('app.subtitle')}</span>
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
            {getHeaderTitle()}
          </span>
          <Dropdown menu={{ items: languageItems }} placement="bottomRight">
            <Button type="text" icon={<GlobalOutlined />}>
              {i18n.language === 'zh' ? '中文' : 'EN'}
            </Button>
          </Dropdown>
        </Header>
        <Content style={{ background: '#f5f5f5', minHeight: 280 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/products" element={<Products />} />
            <Route path="/suppliers" element={<Suppliers />} />
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
