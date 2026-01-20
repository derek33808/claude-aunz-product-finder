import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Space } from 'antd';
import { ShoppingOutlined, RiseOutlined, FileTextOutlined, GlobalOutlined, ReloadOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useNavigate } from 'react-router-dom';
import { productsApi, reportsApi, trendsApi } from '../services/api';
import type { Product, Report } from '../types';

const Dashboard = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const [trendData, setTrendData] = useState<any>(null);

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

  const productColumns = [
    { title: 'Product', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: 'Platform', dataIndex: 'platform', key: 'platform', render: (p: string) => <Tag color={platformColors[p] || 'default'}>{p.toUpperCase()}</Tag> },
    { title: 'Price', dataIndex: 'price', key: 'price', render: (price: number | string, record: Product) => price ? `${record.currency} ${Number(price).toFixed(2)}` : '-' },
    { title: 'Rating', dataIndex: 'rating', key: 'rating', render: (r: number) => r ? `⭐ ${r.toFixed(1)}` : '-' },
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
        <h1 style={{ margin: 0 }}>Dashboard</h1>
        <Button icon={<ReloadOutlined />} onClick={loadDashboardData} loading={loading}>Refresh</Button>
      </div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}><Card><Statistic title="Total Products" value={products.length} prefix={<ShoppingOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title="Reports Generated" value={reports.length} prefix={<FileTextOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title="Platforms" value={4} prefix={<GlobalOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title="Trending" value="Active" prefix={<RiseOutlined />} valueStyle={{ color: '#3f8600' }} /></Card></Col>
      </Row>
      <Row gutter={16}>
        <Col span={12}>
          <Card title="Google Trends - AU" extra={<Tag color="blue">Sample</Tag>}>
            {trendData?.data?.length ? <ReactECharts option={getTrendChartOption()} style={{ height: 300 }} /> : <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>No trend data</div>}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Recent Reports" extra={<Button type="link" onClick={() => navigate('/reports')}>View All</Button>}>
            {reports.length > 0 ? (
              <Table dataSource={reports} rowKey="id" pagination={false} size="small" columns={[
                { title: 'Title', dataIndex: 'title', key: 'title', ellipsis: true },
                { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={s === 'completed' ? 'green' : 'blue'}>{s}</Tag> },
                { title: 'Score', dataIndex: 'overall_score', key: 'score', render: (s: number) => s ? `${s}/100` : '-' },
              ]} />
            ) : <div style={{ textAlign: 'center', padding: 40 }}>No reports yet</div>}
          </Card>
        </Col>
      </Row>
      <Card title="Recent Products" style={{ marginTop: 16 }}>
        <Table dataSource={products} columns={productColumns} rowKey="id" pagination={false} loading={loading} />
      </Card>
    </div>
  );
};

export default Dashboard;
