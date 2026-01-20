import { useState } from 'react';
import { Card, Input, Select, Button, Row, Col, Tag, Table, message, Space } from 'antd';
import { SearchOutlined, GlobalOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { trendsApi } from '../services/api';

const { Search } = Input;
const { Option } = Select;

const Trends = () => {
  const [keyword, setKeyword] = useState('');
  const [region, setRegion] = useState('AU');
  const [loading, setLoading] = useState(false);
  const [trendData, setTrendData] = useState<any>(null);
  const [relatedQueries, setRelatedQueries] = useState<any>(null);
  const [comparison, setComparison] = useState<any>(null);

  const handleSearch = async () => {
    if (!keyword.trim()) { message.warning('Please enter a keyword'); return; }
    setLoading(true);
    try {
      const [interest, related] = await Promise.all([
        trendsApi.getInterest(keyword, region),
        trendsApi.getRelatedQueries(keyword, region),
      ]);
      setTrendData(interest);
      setRelatedQueries(related);
    } catch (error) { message.error('Failed to fetch trends data'); }
    finally { setLoading(false); }
  };

  const handleCompare = async () => {
    if (!keyword.includes(',')) { message.warning('Enter multiple keywords separated by commas'); return; }
    setLoading(true);
    try {
      const data = await trendsApi.compare(keyword, region);
      setComparison(data);
    } catch (error) { message.error('Failed to compare keywords'); }
    finally { setLoading(false); }
  };

  const getChartOption = () => {
    if (!trendData?.data?.length) return {};
    const dates = trendData.data.map((d: any) => d.date);
    const kw = trendData.keywords?.[0] || keyword;
    const values = trendData.data.map((d: any) => d[kw] || 0);
    return {
      title: { text: 'Interest Over Time', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: dates, axisLabel: { rotate: 45 } },
      yAxis: { type: 'value', name: 'Interest', max: 100 },
      series: [{ name: kw, type: 'line', data: values, smooth: true, areaStyle: { opacity: 0.3 }, itemStyle: { color: '#1890ff' } }],
    };
  };

  const getCompareChartOption = () => {
    if (!comparison?.comparison?.length) return {};
    const keywords = comparison.comparison.map((c: any) => c.keyword);
    const values = comparison.comparison.map((c: any) => c.average_interest);
    return {
      title: { text: 'Keyword Comparison', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: keywords },
      yAxis: { type: 'value', name: 'Average Interest' },
      series: [{ type: 'bar', data: values, itemStyle: { color: '#52c41a' } }],
    };
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>Google Trends Analysis</h1>
      
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={10}>
            <Search placeholder="Enter keyword (or comma-separated for comparison)" value={keyword}
              onChange={(e) => setKeyword(e.target.value)} onSearch={handleSearch}
              enterButton={<><SearchOutlined /> Search</>} size="large" />
          </Col>
          <Col span={4}>
            <Select value={region} onChange={setRegion} size="large" style={{ width: '100%' }}>
              <Option value="AU"><GlobalOutlined /> Australia</Option>
              <Option value="NZ"><GlobalOutlined /> New Zealand</Option>
            </Select>
          </Col>
          <Col span={6}>
            <Space>
              <Button onClick={handleSearch} type="primary" loading={loading}>Get Trends</Button>
              <Button onClick={handleCompare} loading={loading}>Compare Keywords</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        <Col span={16}>
          <Card title="Interest Over Time">
            {trendData?.data?.length ? (
              <ReactECharts option={getChartOption()} style={{ height: 400 }} />
            ) : (
              <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                Enter a keyword and click Search to see trends data
              </div>
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Related Queries" style={{ marginBottom: 16 }}>
            {relatedQueries ? (
              <>
                <h4>Top Queries</h4>
                {relatedQueries.top?.slice(0, 5).map((q: any, i: number) => (
                  <Tag key={i} style={{ marginBottom: 4 }}>{q.query} ({q.value})</Tag>
                ))}
                <h4 style={{ marginTop: 16 }}>Rising Queries</h4>
                {relatedQueries.rising?.slice(0, 5).map((q: any, i: number) => (
                  <Tag key={i} color="green" style={{ marginBottom: 4 }}>{q.query} ({q.value})</Tag>
                ))}
              </>
            ) : <div style={{ color: '#999' }}>Search to see related queries</div>}
          </Card>
          <Card title="Region Info">
            <p><strong>Current Region:</strong> <Tag color="blue">{region === 'AU' ? 'Australia' : 'New Zealand'}</Tag></p>
            <p><strong>Keyword:</strong> {keyword || '-'}</p>
          </Card>
        </Col>
      </Row>

      {comparison && (
        <Card title="Keyword Comparison" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <ReactECharts option={getCompareChartOption()} style={{ height: 300 }} />
            </Col>
            <Col span={12}>
              <Table dataSource={comparison.comparison} rowKey="keyword" pagination={false} columns={[
                { title: 'Keyword', dataIndex: 'keyword', key: 'keyword' },
                { title: 'Avg Interest', dataIndex: 'average_interest', key: 'avg', render: (v: number) => v.toFixed(1) },
                { title: 'Max', dataIndex: 'max_interest', key: 'max' },
                { title: 'Current', dataIndex: 'current_interest', key: 'current' },
              ]} />
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );
};

export default Trends;
