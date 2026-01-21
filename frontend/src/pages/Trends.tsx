import { useState } from 'react';
import { Card, Input, Select, Button, Row, Col, Tag, Table, message, Space, Alert } from 'antd';
import { SearchOutlined, GlobalOutlined, InfoCircleOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useTranslation } from 'react-i18next';
import { trendsApi } from '../services/api';

const { Search } = Input;
const { Option } = Select;

const Trends = () => {
  const { t } = useTranslation();
  const [keyword, setKeyword] = useState('');
  const [region, setRegion] = useState('AU');
  const [loading, setLoading] = useState(false);
  const [trendData, setTrendData] = useState<any>(null);
  const [relatedQueries, setRelatedQueries] = useState<any>(null);
  const [comparison, setComparison] = useState<any>(null);

  const handleSearch = async () => {
    if (!keyword.trim()) { message.warning(t('trends.enterKeyword')); return; }
    setLoading(true);
    try {
      const [interest, related] = await Promise.all([
        trendsApi.getInterest(keyword, region),
        trendsApi.getRelatedQueries(keyword, region),
      ]);
      setTrendData(interest);
      setRelatedQueries(related);
    } catch (error) { message.error(t('trends.analysisFailed')); }
    finally { setLoading(false); }
  };

  const handleCompare = async () => {
    if (!keyword.includes(',')) { message.warning(t('trends.enterMultipleKeywords')); return; }
    setLoading(true);
    try {
      const data = await trendsApi.compare(keyword, region);
      setComparison(data);
    } catch (error) { message.error(t('trends.analysisFailed')); }
    finally { setLoading(false); }
  };

  const getChartOption = () => {
    if (!trendData?.data?.length) return {};
    const dates = trendData.data.map((d: any) => d.date);
    const kw = trendData.keywords?.[0] || keyword;
    const values = trendData.data.map((d: any) => d[kw] || 0);
    return {
      title: { text: t('trends.interestOverTime'), left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: { rotate: 45 },
        name: t('trends.xAxisLabel'),
        nameLocation: 'middle',
        nameGap: 35
      },
      yAxis: {
        type: 'value',
        name: t('trends.yAxisLabel'),
        max: 100,
        nameLocation: 'middle',
        nameGap: 50,
        nameRotate: 90
      },
      series: [{ name: kw, type: 'line', data: values, smooth: true, areaStyle: { opacity: 0.3 }, itemStyle: { color: '#1890ff' } }],
      grid: { left: 80, right: 20, bottom: 60, top: 60 }
    };
  };

  const getCompareChartOption = () => {
    if (!comparison?.comparison?.length) return {};
    const keywords = comparison.comparison.map((c: any) => c.keyword);
    const values = comparison.comparison.map((c: any) => c.average_interest);
    return {
      title: { text: t('trends.keywordComparison'), left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: keywords },
      yAxis: {
        type: 'value',
        name: t('trends.yAxisLabel'),
        nameLocation: 'middle',
        nameGap: 50,
        nameRotate: 90,
        max: 100
      },
      series: [{ type: 'bar', data: values, itemStyle: { color: '#52c41a' } }],
      grid: { left: 80, right: 20, bottom: 30, top: 60 }
    };
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>{t('trends.title')}</h1>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={10}>
            <Search placeholder={t('trends.keywordPlaceholder')} value={keyword}
              onChange={(e) => setKeyword(e.target.value)} onSearch={handleSearch}
              enterButton={<><SearchOutlined /> {t('trends.analyze')}</>} size="large" />
          </Col>
          <Col span={4}>
            <Select value={region} onChange={setRegion} size="large" style={{ width: '100%' }}>
              <Option value="AU"><GlobalOutlined /> {t('trends.australia')}</Option>
              <Option value="NZ"><GlobalOutlined /> {t('trends.newZealand')}</Option>
            </Select>
          </Col>
          <Col span={6}>
            <Space>
              <Button onClick={handleSearch} type="primary" loading={loading}>{t('trends.analyze')}</Button>
              <Button onClick={handleCompare} loading={loading}>{t('trends.compareKeywords')}</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        <Col span={16}>
          <Card title={t('trends.interestOverTime')}>
            {trendData?.data?.length ? (
              <>
                <ReactECharts option={getChartOption()} style={{ height: 400 }} />
                <Alert
                  message={<><InfoCircleOutlined style={{ marginRight: 8 }} />{t('trends.chartExplanation')}</>}
                  type="info"
                  style={{ marginTop: 16 }}
                  showIcon={false}
                />
              </>
            ) : (
              <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                {t('trends.noData')}
              </div>
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card title={t('trends.relatedQueries')} style={{ marginBottom: 16 }}>
            {relatedQueries ? (
              <>
                <h4>{t('trends.topQueries')}</h4>
                {relatedQueries.top?.slice(0, 5).map((q: any, i: number) => (
                  <Tag key={i} style={{ marginBottom: 4 }}>{q.query} ({q.value})</Tag>
                ))}
                <h4 style={{ marginTop: 16 }}>{t('trends.risingQueries')}</h4>
                {relatedQueries.rising?.slice(0, 5).map((q: any, i: number) => (
                  <Tag key={i} color="green" style={{ marginBottom: 4 }}>{q.query} ({q.value})</Tag>
                ))}
              </>
            ) : <div style={{ color: '#999' }}>{t('trends.noData')}</div>}
          </Card>
          <Card title={t('trends.region')}>
            <p><strong>{t('trends.region')}:</strong> <Tag color="blue">{region === 'AU' ? t('trends.australia') : t('trends.newZealand')}</Tag></p>
            <p><strong>{t('trends.keyword')}:</strong> {keyword || '-'}</p>
          </Card>
        </Col>
      </Row>

      {comparison && (
        <Card title={t('trends.keywordComparison')} style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <ReactECharts option={getCompareChartOption()} style={{ height: 300 }} />
              <Alert
                message={<><InfoCircleOutlined style={{ marginRight: 8 }} />{t('trends.chartExplanation')}</>}
                type="info"
                style={{ marginTop: 8 }}
                showIcon={false}
              />
            </Col>
            <Col span={12}>
              <Table dataSource={comparison.comparison} rowKey="keyword" pagination={false} columns={[
                { title: t('trends.keyword'), dataIndex: 'keyword', key: 'keyword' },
                { title: t('trends.avgInterest'), dataIndex: 'average_interest', key: 'avg', render: (v: number) => v.toFixed(1) },
                { title: t('trends.maxInterest'), dataIndex: 'max_interest', key: 'max' },
                { title: t('trends.currentInterest'), dataIndex: 'current_interest', key: 'current' },
              ]} />
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );
};

export default Trends;
