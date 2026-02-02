import { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Tag, Input, Select, Image, Statistic, Space, Button, Typography, message, Spin, Progress, Segmented, Alert, Tooltip } from 'antd';
import { ShopOutlined, SearchOutlined, ReloadOutlined, DollarOutlined, LinkOutlined, TrophyOutlined, FireOutlined, RocketOutlined, GlobalOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { supabase } from '../services/supabase';

const { Title, Text } = Typography;
const { Search } = Input;

// API base URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface RankingItem {
  rank: number;
  keyword: string;
  category_zh: string;
  category_en: string;
  total_score: number;
  scores: {
    demand: number;
    trend: number;
    profit: number;
    competition: number;
  };
  platform_stats: {
    trademe?: { listings: number };
    amazon?: { listings: number; price_range?: { min: number; max: number; avg: number } };
    ebay?: { listings: number };
    temu?: { listings: number; price_range?: { min: number; max: number; avg: number } };
  };
  trend_info: {
    direction: string;
    current_interest: number;
  };
  supplier_info: {
    cost_price_cny: number;
    product_count: number;
    top_product?: {
      title: string;
      price: number;
      product_url: string;
    };
  };
  profit_analysis: {
    cost_cny: number;
    market_price_local: number;
    profit_margin_percent: number;
  };
}

interface RankingResult {
  market: string;
  rankings: RankingItem[];
  generated_at: string;
  elapsed_seconds: number;
  data_sources: {
    trademe: boolean;
    amazon_au: boolean;
    ebay: boolean;
    temu: boolean;
    google_trends: boolean;
    suppliers_1688: boolean;
  };
}

interface Supplier1688 {
  id: string;
  title: string;
  price: number;
  product_url: string;
  image_url: string;
  sold_count: number;
  search_keyword: string;
  scraped_at: string;
}

interface KeywordStats {
  keyword: string;
  count: number;
}

const Suppliers = () => {
  const { t } = useTranslation();
  const [suppliers, setSuppliers] = useState<Supplier1688[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [keywords, setKeywords] = useState<KeywordStats[]>([]);
  const [selectedKeyword, setSelectedKeyword] = useState<string>('');
  const [searchText, setSearchText] = useState('');

  // New state for ranking
  const [market, setMarket] = useState<'NZ' | 'AU'>('NZ');
  const [rankingData, setRankingData] = useState<RankingResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [expandedRank, setExpandedRank] = useState<number | null>(null);

  useEffect(() => {
    loadKeywords();
    loadSuppliers();
  }, []);

  const loadKeywords = async () => {
    try {
      const { data, error } = await supabase
        .from('suppliers_1688')
        .select('search_keyword');

      if (error) throw error;

      // Count by keyword
      const keywordCounts: Record<string, number> = {};
      data?.forEach((item: { search_keyword: string }) => {
        const kw = item.search_keyword || 'unknown';
        keywordCounts[kw] = (keywordCounts[kw] || 0) + 1;
      });

      const stats = Object.entries(keywordCounts).map(([keyword, count]) => ({
        keyword,
        count,
      })).sort((a, b) => b.count - a.count);

      setKeywords(stats);
      setTotalCount(data?.length || 0);
    } catch (error) {
      console.error('Failed to load keywords:', error);
    }
  };

  const loadSuppliers = async (keyword?: string, search?: string) => {
    setLoading(true);
    try {
      let query = supabase
        .from('suppliers_1688')
        .select('*')
        .order('price', { ascending: true })
        .limit(50);

      if (keyword) {
        query = query.eq('search_keyword', keyword);
      }

      if (search) {
        query = query.ilike('title', `%${search}%`);
      }

      const { data, error } = await query;

      if (error) throw error;
      setSuppliers(data || []);
    } catch (error) {
      console.error('Failed to load suppliers:', error);
      message.error('加载供应商数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleKeywordChange = (value: string) => {
    setSelectedKeyword(value);
    loadSuppliers(value, searchText);
  };

  const handleSearch = (value: string) => {
    setSearchText(value);
    loadSuppliers(selectedKeyword, value);
  };

  // One-click ranking calculation
  const handleCalculateRanking = async () => {
    setIsCalculating(true);
    message.loading({ content: `正在采集 ${market} 市场数据...`, key: 'ranking', duration: 0 });

    try {
      const response = await fetch(`${API_BASE}/api/ranking/calculate?market=${market}`, {
        method: 'POST',
      });

      const result = await response.json();

      if (result.success) {
        setRankingData(result.data);
        message.success({ content: `${market} 市场排名计算完成！`, key: 'ranking' });
      } else {
        throw new Error(result.error || 'Failed to calculate rankings');
      }
    } catch (error) {
      console.error('Ranking calculation error:', error);
      message.error({ content: '排名计算失败，请确保后端服务正在运行', key: 'ranking' });
    } finally {
      setIsCalculating(false);
    }
  };

  const columns = [
    {
      title: '图片',
      dataIndex: 'image_url',
      key: 'image',
      width: 80,
      render: (url: string) => (
        <Image
          src={url}
          alt="product"
          width={60}
          height={60}
          style={{ objectFit: 'cover', borderRadius: 4 }}
          fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        />
      ),
    },
    {
      title: '产品名称',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (text: string, record: Supplier1688) => (
        <a href={record.product_url} target="_blank" rel="noopener noreferrer">
          {text}
        </a>
      ),
    },
    {
      title: '类别',
      dataIndex: 'search_keyword',
      key: 'keyword',
      width: 100,
      render: (keyword: string) => <Tag color="blue">{keyword}</Tag>,
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      sorter: (a: Supplier1688, b: Supplier1688) => a.price - b.price,
      render: (price: number) => (
        <Text strong style={{ color: '#f5222d' }}>¥{price.toFixed(2)}</Text>
      ),
    },
    {
      title: `建议零售价(${market === 'NZ' ? 'NZ$' : 'AU$'})`,
      key: 'retail_price',
      width: 140,
      render: (_: unknown, record: Supplier1688) => {
        const rate = market === 'NZ' ? 0.23 : 0.21;
        const low = (record.price * rate * 3).toFixed(0);
        const high = (record.price * rate * 5).toFixed(0);
        return <Text type="success">${low} - ${high}</Text>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: Supplier1688) => (
        <Button
          type="link"
          icon={<LinkOutlined />}
          href={record.product_url}
          target="_blank"
        >
          查看
        </Button>
      ),
    },
  ];

  const renderRankingCard = (item: RankingItem) => {
    const isExpanded = expandedRank === item.rank;
    const currency = market === 'NZ' ? 'NZ$' : 'AU$';

    return (
      <Card
        key={item.rank}
        style={{
          marginBottom: 16,
          border: item.rank <= 3 ? '2px solid #f5222d' : '1px solid #d9d9d9',
          background: item.rank <= 3 ? '#fff7e6' : '#fff'
        }}
        hoverable
        onClick={() => setExpandedRank(isExpanded ? null : item.rank)}
      >
        <Row gutter={16} align="middle">
          <Col span={1}>
            <div style={{
              width: 36,
              height: 36,
              borderRadius: '50%',
              background: item.rank <= 3 ? '#f5222d' : '#1890ff',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 18,
              fontWeight: 'bold',
            }}>
              {item.rank}
            </div>
          </Col>
          <Col span={5}>
            <Text strong style={{ fontSize: 16 }}>{item.category_zh}</Text>
            <br />
            <Text type="secondary">{item.category_en}</Text>
          </Col>
          <Col span={3}>
            <Text type="secondary">综合评分</Text>
            <br />
            <Text strong style={{ color: '#f5222d', fontSize: 24 }}>{item.total_score}</Text>
          </Col>
          <Col span={4}>
            <Text type="secondary">1688采购价</Text>
            <br />
            <Text strong style={{ color: '#f5222d' }}>¥{item.supplier_info.cost_price_cny || '-'}</Text>
          </Col>
          <Col span={4}>
            <Text type="secondary">市场均价</Text>
            <br />
            <Text strong style={{ color: '#52c41a' }}>{currency}{item.profit_analysis.market_price_local || '-'}</Text>
          </Col>
          <Col span={3}>
            <Text type="secondary">利润率</Text>
            <br />
            <Text strong style={{ color: item.profit_analysis.profit_margin_percent > 100 ? '#52c41a' : '#faad14' }}>
              {item.profit_analysis.profit_margin_percent > 0 ? `${item.profit_analysis.profit_margin_percent}%` : '-'}
            </Text>
          </Col>
          <Col span={3}>
            <Text type="secondary">趋势</Text>
            <br />
            {item.trend_info.direction === 'up' ? (
              <Tag color="green" icon={<RiseOutlined />}>上升</Tag>
            ) : (
              <Tag color="orange" icon={<FallOutlined />}>平稳</Tag>
            )}
          </Col>
          <Col span={1}>
            {item.supplier_info.top_product && (
              <Button
                type="primary"
                size="small"
                icon={<LinkOutlined />}
                href={item.supplier_info.top_product.product_url}
                target="_blank"
                onClick={(e) => e.stopPropagation()}
              />
            )}
          </Col>
        </Row>

        {isExpanded && (
          <div style={{ marginTop: 16, padding: 16, background: '#fafafa', borderRadius: 8 }}>
            {/* Score breakdown */}
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Card size="small" title="需求评分 (40%)">
                  <Progress percent={item.scores.demand} size="small" />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small" title="趋势评分 (20%)">
                  <Progress percent={item.scores.trend} size="small" status={item.trend_info.direction === 'up' ? 'active' : 'normal'} />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small" title="利润评分 (25%)">
                  <Progress percent={item.scores.profit} size="small" strokeColor="#52c41a" />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small" title="竞争评分 (15%)">
                  <Progress percent={item.scores.competition} size="small" strokeColor="#faad14" />
                </Card>
              </Col>
            </Row>

            {/* Platform data */}
            <Card size="small" title="各平台数据" style={{ marginTop: 16 }}>
              <Row gutter={16}>
                {market === 'NZ' && item.platform_stats.trademe && (
                  <Col span={6}>
                    <Statistic
                      title="TradeMe"
                      value={item.platform_stats.trademe.listings}
                      suffix="件在售"
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Col>
                )}
                {item.platform_stats.amazon && (
                  <Col span={6}>
                    <Statistic
                      title="Amazon AU"
                      value={item.platform_stats.amazon.listings}
                      suffix="件"
                      valueStyle={{ color: '#ff9900' }}
                    />
                    {item.platform_stats.amazon.price_range && (
                      <Text type="secondary">
                        {currency}{item.platform_stats.amazon.price_range.min?.toFixed(0)} - {currency}{item.platform_stats.amazon.price_range.max?.toFixed(0)}
                      </Text>
                    )}
                  </Col>
                )}
                {item.platform_stats.ebay && (
                  <Col span={6}>
                    <Statistic
                      title="eBay"
                      value={item.platform_stats.ebay.listings}
                      suffix="件"
                      valueStyle={{ color: '#e53238' }}
                    />
                  </Col>
                )}
                {item.platform_stats.temu && (
                  <Col span={6}>
                    <Statistic
                      title="Temu"
                      value={item.platform_stats.temu.listings}
                      suffix="件"
                      valueStyle={{ color: '#ff6f00' }}
                    />
                    {item.platform_stats.temu.price_range && (
                      <Text type="secondary">
                        {currency}{item.platform_stats.temu.price_range.min?.toFixed(0)} - {currency}{item.platform_stats.temu.price_range.max?.toFixed(0)}
                      </Text>
                    )}
                  </Col>
                )}
              </Row>
            </Card>

            {/* Supplier info */}
            {item.supplier_info.top_product && (
              <Card size="small" title="推荐供应商 (1688)" style={{ marginTop: 16 }}>
                <Row align="middle">
                  <Col span={16}>
                    <Text>{item.supplier_info.top_product.title}</Text>
                  </Col>
                  <Col span={4}>
                    <Text strong style={{ color: '#f5222d' }}>¥{item.supplier_info.top_product.price}</Text>
                  </Col>
                  <Col span={4}>
                    <Button type="link" href={item.supplier_info.top_product.product_url} target="_blank">
                      查看供应商
                    </Button>
                  </Col>
                </Row>
              </Card>
            )}
          </div>
        )}
      </Card>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>
        <ShopOutlined /> 智能选品系统
      </Title>

      {/* Market Selection & One-Click Ranking */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col span={8}>
            <Text strong style={{ marginRight: 16 }}>目标市场：</Text>
            <Segmented
              value={market}
              onChange={(value) => setMarket(value as 'NZ' | 'AU')}
              options={[
                { label: '🇳🇿 新西兰', value: 'NZ' },
                { label: '🇦🇺 澳大利亚', value: 'AU' },
              ]}
              size="large"
            />
          </Col>
          <Col span={8}>
            <Button
              type="primary"
              size="large"
              icon={<RocketOutlined />}
              onClick={handleCalculateRanking}
              loading={isCalculating}
              style={{ background: '#f5222d', borderColor: '#f5222d' }}
            >
              一键选品
            </Button>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              自动采集多平台数据并计算排名
            </Text>
          </Col>
          <Col span={8}>
            {rankingData && (
              <Text type="secondary">
                数据更新时间: {new Date(rankingData.generated_at).toLocaleString()}
                <br />
                采集耗时: {rankingData.elapsed_seconds.toFixed(1)}秒
              </Text>
            )}
          </Col>
        </Row>
      </Card>

      {/* Ranking Results */}
      {isCalculating ? (
        <Card style={{ marginBottom: 24, textAlign: 'center', padding: 48 }}>
          <Spin size="large" />
          <Title level={4} style={{ marginTop: 16 }}>正在采集数据...</Title>
          <Text type="secondary">
            正在从 TradeMe、Amazon、eBay、Temu、Google Trends 和 1688 采集数据
          </Text>
          <br />
          <Text type="secondary">这可能需要1-2分钟，请耐心等待</Text>
        </Card>
      ) : rankingData ? (
        <Card
          style={{ marginBottom: 24 }}
          title={
            <span>
              <TrophyOutlined style={{ color: '#faad14', marginRight: 8 }} />
              {market === 'NZ' ? '🇳🇿 新西兰' : '🇦🇺 澳大利亚'} 市场 TOP 10 选品推荐
              <Tag color="red" style={{ marginLeft: 8 }}>
                <FireOutlined /> 实时数据
              </Tag>
            </span>
          }
          extra={<Text type="secondary">点击卡片查看详细分析</Text>}
        >
          <div style={{ marginBottom: 16, padding: 12, background: 'linear-gradient(135deg, #e6f7ff 0%, #f6ffed 100%)', borderRadius: 8 }}>
            <Row gutter={16}>
              <Col span={8}>
                <Text strong>📊 数据来源：</Text>
                <Text>
                  {market === 'NZ' && 'TradeMe + '}
                  Amazon + eBay + Temu + Google Trends + 1688
                </Text>
              </Col>
              <Col span={8}>
                <Text strong>🎯 目标市场：</Text>
                <Text>{market === 'NZ' ? '🇳🇿 新西兰' : '🇦🇺 澳大利亚'}</Text>
              </Col>
              <Col span={8}>
                <Text strong>📈 排名算法：</Text>
                <Tooltip title="需求40% + 趋势20% + 利润25% + 竞争15%">
                  <Text style={{ cursor: 'help', textDecoration: 'underline dotted' }}>
                    综合评分模型
                  </Text>
                </Tooltip>
              </Col>
            </Row>
          </div>

          {rankingData.rankings.map(item => renderRankingCard(item))}
        </Card>
      ) : (
        <Alert
          message="点击「一键选品」开始分析"
          description={`系统将自动从 ${market === 'NZ' ? 'TradeMe、' : ''}Amazon、eBay、Temu、Google Trends 采集实时数据，并结合1688供应商价格计算综合排名。`}
          type="info"
          showIcon
          icon={<RocketOutlined />}
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Stats Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="1688供应商总数"
              value={totalCount}
              prefix={<ShopOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="产品类别"
              value={keywords.length}
              prefix={<SearchOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="最低采购价"
              value={suppliers.length > 0 ? Math.min(...suppliers.map(s => s.price)) : 0}
              prefix={<DollarOutlined />}
              suffix="¥"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均采购价"
              value={suppliers.length > 0 ? (suppliers.reduce((acc, s) => acc + s.price, 0) / suppliers.length).toFixed(1) : 0}
              prefix={<DollarOutlined />}
              suffix="¥"
            />
          </Card>
        </Col>
      </Row>

      {/* Filter Bar */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="middle">
          <Select
            placeholder="选择类别"
            style={{ width: 200 }}
            allowClear
            onChange={handleKeywordChange}
            value={selectedKeyword || undefined}
          >
            {keywords.map(k => (
              <Select.Option key={k.keyword} value={k.keyword}>
                {k.keyword} ({k.count})
              </Select.Option>
            ))}
          </Select>
          <Search
            placeholder="搜索产品名称"
            style={{ width: 300 }}
            onSearch={handleSearch}
            allowClear
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              setSelectedKeyword('');
              setSearchText('');
              loadSuppliers();
            }}
          >
            重置
          </Button>
        </Space>
      </Card>

      {/* Suppliers Table */}
      <Card title={`1688供应商列表 (${suppliers.length})`}>
        <Table
          columns={columns}
          dataSource={suppliers}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>
    </div>
  );
};

export default Suppliers;
