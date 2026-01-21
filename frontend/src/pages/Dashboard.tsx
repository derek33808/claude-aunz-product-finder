import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Space } from 'antd';
import { ShoppingOutlined, RiseOutlined, FileTextOutlined, GlobalOutlined, ReloadOutlined, FireOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { productsApi, reportsApi, trendsApi } from '../services/api';
import type { Product, Report } from '../types';

const Dashboard = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [products, setProducts] = useState<Product[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const [trendData, setTrendData] = useState<any>(null);
  const [hotProducts, setHotProducts] = useState<(Product & { hot_score: number })[]>([]);
  const [hotLoading, setHotLoading] = useState(false);

  useEffect(() => { loadDashboardData(); }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const productData = await productsApi.search({ page_size: 10 });
      setProducts(productData);
      const reportData = await reportsApi.list({ page_size: 5 });
      setReports(reportData);
      try {
        const trends = await trendsApi.getInterest('wireless earbuds', 'AU');
        setTrendData(trends);
      } catch (e) { console.log('Trends not available'); }
    } catch (error) { console.error('Failed to load dashboard data:', error); }
    finally { setLoading(false); }
  };

  const platformColors: Record<string, string> = { ebay_au: 'blue', ebay_nz: 'green', amazon_au: 'orange', trademe: 'purple' };

  const findHotProducts = async () => {
    setHotLoading(true);
    try {
      const data = await productsApi.getHotProducts(10);
      setHotProducts(data);
    } catch (error) {
      console.error('Failed to get hot products:', error);
    } finally {
      setHotLoading(false);
    }
  };

  const productColumns = [
    { title: t('products.product'), dataIndex: 'title', key: 'title', ellipsis: true },
    { title: t('products.platform'), dataIndex: 'platform', key: 'platform', render: (p: string) => <Tag color={platformColors[p] || 'default'}>{p.toUpperCase()}</Tag> },
    { title: t('products.price'), dataIndex: 'price', key: 'price', render: (price: number | string, record: Product) => price ? `${record.currency} ${Number(price).toFixed(2)}` : '-' },
    { title: t('products.rating'), dataIndex: 'rating', key: 'rating', render: (r: number) => r ? `⭐ ${r.toFixed(1)}` : '-' },
  ];

  const hotProductColumns = [
    { title: t('products.product'), dataIndex: 'title', key: 'title', ellipsis: true, render: (text: string, record: Product) => record.product_url ? <a href={record.product_url} target="_blank" rel="noreferrer">{text}</a> : text },
    { title: t('products.platform'), dataIndex: 'platform', key: 'platform', width: 100, render: (p: string) => <Tag color={platformColors[p] || 'default'}>{p.toUpperCase()}</Tag> },
    { title: t('products.price'), dataIndex: 'price', key: 'price', width: 100, render: (price: number | string, record: Product) => price ? `${record.currency} ${Number(price).toFixed(2)}` : '-' },
    { title: t('products.rating'), dataIndex: 'rating', key: 'rating', width: 80, render: (r: number) => r ? `⭐ ${r.toFixed(1)}` : '-' },
    { title: t('dashboard.hotScore'), dataIndex: 'hot_score', key: 'hot_score', width: 100, render: (score: number) => <Tag color="red">{score.toFixed(0)}</Tag> },
  ];

  const getTrendChartOption = () => {
    if (!trendData?.data?.length) return {};
    const dates = trendData.data.map((d: any) => d.date);
    const values = trendData.data.map((d: any) => d[trendData.keywords?.[0]] || 0);
    return {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: dates, axisLabel: { rotate: 45 } },
      yAxis: { type: 'value', name: 'Interest' },
      series: [{ name: trendData.keywords?.[0] || 'Trend', type: 'line', data: values, smooth: true, areaStyle: { opacity: 0.3 } }],
    };
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>{t('dashboard.title')}</h1>
        <Space>
          <Button type="primary" icon={<FireOutlined />} onClick={findHotProducts} loading={hotLoading} danger>
            {hotLoading ? t('dashboard.finding') : t('dashboard.findHotProducts')}
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadDashboardData} loading={loading}>{t('dashboard.refresh')}</Button>
        </Space>
      </div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}><Card><Statistic title={t('dashboard.totalProducts')} value={products.length} prefix={<ShoppingOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title={t('dashboard.reportsGenerated')} value={reports.length} prefix={<FileTextOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title={t('dashboard.platforms')} value={4} prefix={<GlobalOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title={t('dashboard.trending')} value={t('dashboard.active')} prefix={<RiseOutlined />} valueStyle={{ color: '#3f8600' }} /></Card></Col>
      </Row>
      {hotProducts.length > 0 && (
        <Card title={<><FireOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />{t('dashboard.topHotProducts')}</>} style={{ marginBottom: 16 }}>
          <Table dataSource={hotProducts} columns={hotProductColumns} rowKey="id" pagination={false} size="small" />
        </Card>
      )}
      <Row gutter={16}>
        <Col span={12}>
          <Card title={t('dashboard.googleTrends')} extra={<Tag color="blue">{t('dashboard.sample')}</Tag>}>
            {trendData?.data?.length ? <ReactECharts option={getTrendChartOption()} style={{ height: 300 }} /> : <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{t('dashboard.noTrendData')}</div>}
          </Card>
        </Col>
        <Col span={12}>
          <Card title={t('dashboard.recentReports')} extra={<Button type="link" onClick={() => navigate('/reports')}>{t('dashboard.viewAll')}</Button>}>
            {reports.length > 0 ? (
              <Table dataSource={reports} rowKey="id" pagination={false} size="small" columns={[
                { title: t('reports.title'), dataIndex: 'title', key: 'title', ellipsis: true },
                { title: t('reports.status'), dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={s === 'completed' ? 'green' : 'blue'}>{s}</Tag> },
                { title: t('reports.score'), dataIndex: 'overall_score', key: 'score', render: (s: number) => s ? `${s}/100` : '-' },
              ]} />
            ) : <div style={{ textAlign: 'center', padding: 40 }}>{t('dashboard.noReports')}</div>}
          </Card>
        </Col>
      </Row>
      <Card title={t('dashboard.recentProducts')} style={{ marginTop: 16 }}>
        <Table dataSource={products} columns={productColumns} rowKey="id" pagination={false} loading={loading} />
      </Card>
    </div>
  );
};

export default Dashboard;
